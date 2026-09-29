from __future__ import annotations

import json
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from xninetzy.db.sqlite import connect, init_db


class AuthSessionStatus(StrEnum):
    CREATED = "created"
    WAITING_FOR_USER = "waiting_for_user"
    CALLBACK_RECEIVED = "callback_received"
    EXCHANGING = "exchanging"
    AUTHENTICATED = "authenticated"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVOKED = "revoked"
    EXPIRED = "expired"


_VALID_TRANSITIONS: dict[AuthSessionStatus, frozenset[AuthSessionStatus]] = {
    AuthSessionStatus.CREATED: frozenset(
        {
            AuthSessionStatus.WAITING_FOR_USER,
            AuthSessionStatus.CALLBACK_RECEIVED,
            AuthSessionStatus.CANCELLED,
            AuthSessionStatus.FAILED,
            AuthSessionStatus.EXPIRED,
        }
    ),
    AuthSessionStatus.WAITING_FOR_USER: frozenset(
        {
            AuthSessionStatus.CALLBACK_RECEIVED,
            AuthSessionStatus.EXCHANGING,
            AuthSessionStatus.AUTHENTICATED,
            AuthSessionStatus.CANCELLED,
            AuthSessionStatus.FAILED,
            AuthSessionStatus.EXPIRED,
        }
    ),
    AuthSessionStatus.CALLBACK_RECEIVED: frozenset(
        {
            AuthSessionStatus.EXCHANGING,
            AuthSessionStatus.AUTHENTICATED,
            AuthSessionStatus.FAILED,
            AuthSessionStatus.EXPIRED,
        }
    ),
    AuthSessionStatus.EXCHANGING: frozenset(
        {
            AuthSessionStatus.AUTHENTICATED,
            AuthSessionStatus.FAILED,
            AuthSessionStatus.EXPIRED,
        }
    ),
    AuthSessionStatus.AUTHENTICATED: frozenset(
        {
            AuthSessionStatus.REVOKED,
            AuthSessionStatus.EXPIRED,
        }
    ),
    AuthSessionStatus.FAILED: frozenset(),
    AuthSessionStatus.CANCELLED: frozenset(),
    AuthSessionStatus.REVOKED: frozenset(),
    AuthSessionStatus.EXPIRED: frozenset(),
}

_SECRET_FIELDS = frozenset({"pkce_verifier", "state_token"})
_lock = threading.RLock()


@dataclass
class AuthSessionRecord:
    session_id: str
    owner: str
    provider: str
    account: str
    method: str
    state: AuthSessionStatus = AuthSessionStatus.CREATED
    scopes: tuple[str, ...] = ()
    state_token: str = ""
    pkce_verifier: str = ""
    authorization_url: str = ""
    redirect_uri: str = ""
    credential_ref: str = ""
    identity: dict = field(default_factory=dict)
    error_code: str = ""
    created_at: str = ""
    updated_at: str = ""
    authenticated_at: str | None = None
    last_validated_at: str | None = None
    expires_at: str | None = None

    def to_safe_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "owner": self.owner,
            "provider": self.provider,
            "account": self.account,
            "method": self.method,
            "state": self.state.value,
            "scopes": list(self.scopes),
            "authorization_url": self.authorization_url,
            "redirect_uri": self.redirect_uri,
            "credential_ref": self.credential_ref,
            "identity": dict(self.identity),
            "error_code": self.error_code,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "authenticated_at": self.authenticated_at,
            "last_validated_at": self.last_validated_at,
            "expires_at": self.expires_at,
            "has_pkce_verifier": bool(self.pkce_verifier),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_table() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                provider TEXT NOT NULL,
                account TEXT NOT NULL,
                method TEXT NOT NULL,
                state TEXT NOT NULL,
                scopes_json TEXT NOT NULL DEFAULT '[]',
                state_token TEXT,
                pkce_verifier TEXT,
                authorization_url TEXT,
                redirect_uri TEXT,
                credential_ref TEXT,
                identity_json TEXT NOT NULL DEFAULT '{}',
                error_code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                authenticated_at TEXT,
                last_validated_at TEXT,
                expires_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_owner "
            "ON auth_sessions(owner, provider, account, state)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_state_token "
            "ON auth_sessions(state_token)"
        )


def new_state_token() -> str:
    return secrets.token_urlsafe(32)


def is_valid_transition(current: AuthSessionStatus, target: AuthSessionStatus) -> bool:
    return target in _VALID_TRANSITIONS.get(current, frozenset())


def _row_to_record(row) -> AuthSessionRecord:
    return AuthSessionRecord(
        session_id=row["session_id"],
        owner=row["owner"],
        provider=row["provider"],
        account=row["account"],
        method=row["method"],
        state=AuthSessionStatus(row["state"]),
        scopes=tuple(json.loads(row["scopes_json"] or "[]")),
        state_token=row["state_token"] or "",
        pkce_verifier=row["pkce_verifier"] or "",
        authorization_url=row["authorization_url"] or "",
        redirect_uri=row["redirect_uri"] or "",
        credential_ref=row["credential_ref"] or "",
        identity=json.loads(row["identity_json"] or "{}"),
        error_code=row["error_code"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        authenticated_at=row["authenticated_at"],
        last_validated_at=row["last_validated_at"],
        expires_at=row["expires_at"],
    )


def create_session(
    *,
    owner: str,
    provider: str,
    account: str = "default",
    method: str = "oauth",
    scopes: tuple[str, ...] | list[str] = (),
    state_token: str | None = None,
    pkce_verifier: str | None = None,
    authorization_url: str | None = None,
    redirect_uri: str | None = None,
    ttl_seconds: int = 900,
) -> AuthSessionRecord:
    _ensure_table()
    now = _now()
    expires = (
        datetime.now(timezone.utc) + timedelta(seconds=max(1, int(ttl_seconds)))
    ).isoformat()
    record = AuthSessionRecord(
        session_id="auth-" + uuid.uuid4().hex,
        owner=(owner or "").strip() or "default",
        provider=provider,
        account=account or "default",
        method=method,
        state=AuthSessionStatus.CREATED,
        scopes=tuple(scopes or ()),
        state_token=state_token or "",
        pkce_verifier=pkce_verifier or "",
        authorization_url=authorization_url or "",
        redirect_uri=redirect_uri or "",
        created_at=now,
        updated_at=now,
        expires_at=expires,
    )
    with _lock, connect() as conn:
        conn.execute(
            """
            INSERT INTO auth_sessions
              (session_id, owner, provider, account, method, state, scopes_json,
               state_token, pkce_verifier, authorization_url, redirect_uri,
               credential_ref, identity_json, error_code, created_at, updated_at,
               authenticated_at, last_validated_at, expires_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                record.session_id,
                record.owner,
                record.provider,
                record.account,
                record.method,
                record.state.value,
                json.dumps(list(record.scopes)),
                record.state_token,
                record.pkce_verifier,
                record.authorization_url,
                record.redirect_uri,
                record.credential_ref,
                json.dumps(record.identity),
                record.error_code,
                record.created_at,
                record.updated_at,
                record.authenticated_at,
                record.last_validated_at,
                record.expires_at,
            ),
        )
    return record


def get_session(session_id: str) -> AuthSessionRecord | None:
    _ensure_table()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM auth_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
    return _row_to_record(row) if row else None


def list_sessions(
    owner: str | None = None,
    provider: str | None = None,
    account: str | None = None,
    state: AuthSessionStatus | None = None,
    limit: int = 100,
) -> list[AuthSessionRecord]:
    _ensure_table()
    clauses: list[str] = []
    params: list[object] = []
    if owner is not None:
        clauses.append("owner=?")
        params.append(owner)
    if provider is not None:
        clauses.append("provider=?")
        params.append(provider)
    if account is not None:
        clauses.append("account=?")
        params.append(account)
    if state is not None:
        clauses.append("state=?")
        params.append(state.value)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    bounded = max(1, min(int(limit), 500))
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM auth_sessions {where} ORDER BY created_at DESC LIMIT ?",
            (*params, bounded),
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def transition(
    session_id: str,
    *,
    to: AuthSessionStatus,
    error_code: str = "",
    credential_ref: str | None = None,
    identity: dict | None = None,
) -> AuthSessionRecord | None:
    _ensure_table()
    with _lock, connect() as conn:
        row = conn.execute(
            "SELECT * FROM auth_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        record = _row_to_record(row)
        if not is_valid_transition(record.state, to):
            return record
        now = _now()
        record.state = to
        record.updated_at = now
        if error_code:
            record.error_code = error_code
        if credential_ref is not None:
            record.credential_ref = credential_ref
        if identity is not None:
            record.identity = identity
        if to is AuthSessionStatus.AUTHENTICATED:
            record.authenticated_at = now
            record.last_validated_at = now
        if to is AuthSessionStatus.REVOKED:
            record.credential_ref = ""
        conn.execute(
            """
            UPDATE auth_sessions
            SET state=?, updated_at=?, error_code=?, credential_ref=?,
                identity_json=?, authenticated_at=?, last_validated_at=?
            WHERE session_id=?
            """,
            (
                record.state.value,
                record.updated_at,
                record.error_code,
                record.credential_ref,
                json.dumps(record.identity),
                record.authenticated_at,
                record.last_validated_at,
                session_id,
            ),
        )
    return record


def find_session_by_state(state_token: str) -> AuthSessionRecord | None:
    if not state_token:
        return None
    _ensure_table()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM auth_sessions WHERE state_token=? ORDER BY created_at DESC LIMIT 1",
            (state_token,),
        ).fetchone()
    return _row_to_record(row) if row else None


def find_active_connection(
    owner: str, provider: str, account: str = "default"
) -> AuthSessionRecord | None:
    _ensure_table()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM auth_sessions
            WHERE owner=? AND provider=? AND account=? AND state=?
            ORDER BY authenticated_at DESC, created_at DESC LIMIT 1
            """,
            (owner, provider, account, AuthSessionStatus.AUTHENTICATED.value),
        ).fetchone()
    return _row_to_record(row) if row else None
