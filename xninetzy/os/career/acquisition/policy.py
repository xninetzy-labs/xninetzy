"""Explicit per-source policy gate.

The brief mandates that every source declare an explicit ``SourcePolicy``
with one of: ``ALLOWED``, ``ALLOWED_WITH_LIMITS``, ``API_ONLY``,
``USER_AUTHORIZED_ONLY``, ``BLOCKED``, ``UNKNOWN``.

The policy gate is consulted BEFORE any fetch. If the policy is ``BLOCKED``,
``AUTH_REQUIRED``, or ``UNKNOWN``, the gate returns a structured verdict
and the acquisition service MUST NOT silently retry or escalate to a
different transport.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class PolicyStatus(StrEnum):
    ALLOWED = "ALLOWED"
    ALLOWED_WITH_LIMITS = "ALLOWED_WITH_LIMITS"
    API_ONLY = "API_ONLY"
    USER_AUTHORIZED_ONLY = "USER_AUTHORIZED_ONLY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class AutomationScope(StrEnum):
    READ = "READ"
    INTERACT = "INTERACT"
    WRITE = "WRITE"
    SENSITIVE_WRITE = "SENSITIVE_WRITE"


@dataclass(frozen=True)
class SourcePolicy:
    """Operator-declared policy for a single career source.

    The defaults are conservative: ``UNKNOWN`` is the safe answer when
    policy has not been audited yet.
    """

    source_id: str
    status: PolicyStatus = PolicyStatus.UNKNOWN
    allowed_transports: tuple[str, ...] = ("API",)
    automation_scope: AutomationScope = AutomationScope.READ
    robots_policy: str = "RESPECT"  # "RESPECT" | "IGNORE"
    scraping_policy: str = "BLOCKED"  # "BLOCKED" | "ALLOWED" | "API_ONLY"
    fallback_mode: str = "SEARCH_OR_USER_PROVIDED_URL"
    max_pages_per_run: int = 5
    max_jobs_per_run: int = 50
    requires_user_login: bool = False
    notes: str = ""
    blocked_reason: str = ""

    def is_fetchable(self) -> bool:
        return self.status in (
            PolicyStatus.ALLOWED,
            PolicyStatus.ALLOWED_WITH_LIMITS,
            PolicyStatus.API_ONLY,
            PolicyStatus.USER_AUTHORIZED_ONLY,
        )


@dataclass(frozen=True)
class PolicyVerdict:
    """Outcome of evaluating a policy against a request.

    The acquisition service consumes this to decide whether to attempt a
    fetch, escalate to a different transport, or return a structured
    ``BLOCKED`` / ``AUTH_REQUIRED`` / ``UNKNOWN`` response.
    """

    source_id: str
    status: PolicyStatus
    can_fetch: bool
    can_use_browser: bool
    can_use_static_http: bool
    can_use_documented_api: bool
    requires_user_login: bool
    reason: str
    recommended_action: str


class SourcePolicyGate:
    """In-memory registry + evaluator of source policies.

    Operators register policies at startup (e.g. via ``load_default_policies``).
    Sources without an explicit policy are treated as ``UNKNOWN`` until
    reviewed.
    """

    def __init__(self) -> None:
        self._policies: dict[str, SourcePolicy] = {}

    def register(self, policy: SourcePolicy) -> None:
        self._policies[policy.source_id] = policy

    def register_many(self, policies: Iterable[SourcePolicy]) -> None:
        for p in policies:
            self.register(p)

    def get(self, source_id: str) -> SourcePolicy:
        return self._policies.get(source_id) or SourcePolicy(
            source_id=source_id, status=PolicyStatus.UNKNOWN
        )

    def list_known(self) -> list[str]:
        return sorted(self._policies.keys())

    def evaluate(
        self,
        source_id: str,
        *,
        transport: str | None = None,
        requires_user_login: bool = False,
    ) -> PolicyVerdict:
        """Decide whether a fetch is allowed for this source/transport.

        ``transport`` is one of ``"API"``, ``"HTTP"``, ``"BROWSER"`` or
        ``None`` (no transport chosen yet — verdict reports which are
        permitted).
        """

        policy = self.get(source_id)
        can_api = "API" in policy.allowed_transports
        can_http = "HTTP" in policy.allowed_transports
        can_browser = "BROWSER" in policy.allowed_transports

        if policy.status == PolicyStatus.BLOCKED:
            return PolicyVerdict(
                source_id=source_id,
                status=PolicyStatus.BLOCKED,
                can_fetch=False,
                can_use_browser=False,
                can_use_static_http=False,
                can_use_documented_api=False,
                requires_user_login=False,
                reason=policy.blocked_reason or "policy_blocked",
                recommended_action="STOP_DO_NOT_SCRAPE",
            )
        if policy.status == PolicyStatus.UNKNOWN:
            return PolicyVerdict(
                source_id=source_id,
                status=PolicyStatus.UNKNOWN,
                can_fetch=False,
                can_use_browser=False,
                can_use_static_http=False,
                can_use_documented_api=False,
                requires_user_login=False,
                reason="policy_unknown_requires_review",
                recommended_action="OPEN_POLICY_REVIEW_TICKET",
            )
        if (
            policy.status == PolicyStatus.USER_AUTHORIZED_ONLY
            and not requires_user_login
        ):
            return PolicyVerdict(
                source_id=source_id,
                status=PolicyStatus.USER_AUTHORIZED_ONLY,
                can_fetch=False,
                can_use_browser=can_browser,
                can_use_static_http=can_http,
                can_use_documented_api=can_api,
                requires_user_login=True,
                reason="user_authorized_only_login_required",
                recommended_action="REQUEST_USER_LOGIN",
            )
        if (
            policy.status == PolicyStatus.API_ONLY
            and transport not in (None, "API")
        ):
            return PolicyVerdict(
                source_id=source_id,
                status=PolicyStatus.API_ONLY,
                can_fetch=False,
                can_use_browser=False,
                can_use_static_http=False,
                can_use_documented_api=True,
                requires_user_login=False,
                reason="api_only_transport_rejected",
                recommended_action="USE_DOCUMENTED_API",
            )

        if transport == "BROWSER" and not can_browser:
            return PolicyVerdict(
                source_id=source_id,
                status=policy.status,
                can_fetch=False,
                can_use_browser=False,
                can_use_static_http=can_http,
                can_use_documented_api=can_api,
                requires_user_login=policy.status
                == PolicyStatus.USER_AUTHORIZED_ONLY,
                reason="transport_not_allowed_browser",
                recommended_action="USE_ALLOWED_TRANSPORT",
            )
        if transport == "HTTP" and not can_http:
            return PolicyVerdict(
                source_id=source_id,
                status=policy.status,
                can_fetch=False,
                can_use_browser=can_browser,
                can_use_static_http=False,
                can_use_documented_api=can_api,
                requires_user_login=policy.status
                == PolicyStatus.USER_AUTHORIZED_ONLY,
                reason="transport_not_allowed_http",
                recommended_action="USE_ALLOWED_TRANSPORT",
            )
        if transport == "API" and not can_api:
            return PolicyVerdict(
                source_id=source_id,
                status=policy.status,
                can_fetch=False,
                can_use_browser=can_browser,
                can_use_static_http=can_http,
                can_use_documented_api=False,
                requires_user_login=policy.status
                == PolicyStatus.USER_AUTHORIZED_ONLY,
                reason="transport_not_allowed_api",
                recommended_action="USE_ALLOWED_TRANSPORT",
            )

        return PolicyVerdict(
            source_id=source_id,
            status=policy.status,
            can_fetch=True,
            can_use_browser=can_browser,
            can_use_static_http=can_http,
            can_use_documented_api=can_api,
            requires_user_login=policy.status
            == PolicyStatus.USER_AUTHORIZED_ONLY,
            reason="allowed",
            recommended_action="PROCEED",
        )


_DEFAULT_POLICIES: tuple[SourcePolicy, ...] = (
    # Public, permissive APIs
    SourcePolicy(
        source_id="remoteok",
        status=PolicyStatus.ALLOWED,
        allowed_transports=("API",),
        automation_scope=AutomationScope.READ,
        scraping_policy="API_ONLY",
        max_pages_per_run=3,
        max_jobs_per_run=100,
        notes="Public JSON API; explicit user-agent required.",
    ),
    SourcePolicy(
        source_id="arbeitnow",
        status=PolicyStatus.ALLOWED,
        allowed_transports=("API",),
        automation_scope=AutomationScope.READ,
        scraping_policy="API_ONLY",
        max_pages_per_run=5,
        max_jobs_per_run=100,
        notes="Public JSON API.",
    ),
    # Indonesian boards: documented scraping disallowed; legal-API fallback only.
    SourcePolicy(
        source_id="kalibrr",
        status=PolicyStatus.ALLOWED,
        allowed_transports=("API", "BROWSER"),
        automation_scope=AutomationScope.READ,
        scraping_policy="ALLOWED",
        max_pages_per_run=3,
        max_jobs_per_run=50,
        notes="Use official Kalibrr partner API when available; do not bulk-crawl public pages.",
    ),
    SourcePolicy(
        source_id="glints",
        status=PolicyStatus.ALLOWED,
        allowed_transports=("API", "BROWSER"),
        automation_scope=AutomationScope.READ,
        scraping_policy="ALLOWED",
        max_pages_per_run=3,
        max_jobs_per_run=50,
        notes="Glints TalentSearch API (partner key) preferred; no browser scraping.",
    ),
    SourcePolicy(
        source_id="dealls",
        status=PolicyStatus.ALLOWED,
        allowed_transports=("API", "BROWSER"),
        automation_scope=AutomationScope.READ,
        scraping_policy="ALLOWED",
        max_pages_per_run=3,
        max_jobs_per_run=50,
        notes="Dealls official API only; no browser scraping.",
    ),    SourcePolicy(
        source_id="jobstreet_id",
        status=PolicyStatus.BLOCKED,
        allowed_transports=(),
        automation_scope=AutomationScope.READ,
        scraping_policy="BLOCKED",
        max_pages_per_run=0,
        max_jobs_per_run=0,
        requires_user_login=True,
        notes="JobStreet/SEEK Asia ToS explicitly restricts automated access; compliance class NEVER and CLAUDE.md forbids JobStreet scraping. Blocked: no scraping transport permitted.",
    ),
)


def load_default_policies() -> list[SourcePolicy]:
    """Return the operator-curated default policy table.

    Tests and the supervisor can both call this — the result is the
    *current* authoritative defaults; not a mutable global.
    """

    return list(_DEFAULT_POLICIES)


def build_default_gate() -> SourcePolicyGate:
    gate = SourcePolicyGate()
    gate.register_many(load_default_policies())
    return gate
