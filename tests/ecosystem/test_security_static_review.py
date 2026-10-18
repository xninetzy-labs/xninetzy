from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

from xninetzy.os.perf import scaling
from xninetzy.os.security import authz, infra_review

SDL = """
type Query {
  me: User
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
}

type Mutation {
  updateUser(id: ID!, input: UserInput!): User!
  adminCreateUser(email: String!, role: Role!): User!
  setRole(userId: ID!, role: Role!): User!
  login(email: String!, password: String!): Session!
  deletePost(id: ID!): Boolean!
}
"""

RESOLVERS = textwrap.dedent("""
    export interface UserRow {
      role: string;
    }

    export const resolvers = {
      Mutation: {
        updateUser: async (_parent, args, ctx) => {
          requireAdmin(ctx);
          assertCanAssignRole(ctx.user, args.input.role);
          return db.user.update({ where: { id: args.id }, data: { role: args.input.role } });
        },
        adminCreateUser: async (_parent, args, ctx) => {
          requireAdmin(ctx);
          return db.user.create({ data: { email: args.email, role: args.role } });
        },
        setRole: async (_parent, args, ctx) => {
          requireAdmin(ctx);
          return db.user.update({ where: { id: args.userId }, data: { role: args.role } });
        },
        login: async (_parent, args, ctx) => {
          const user = await find(args.email);
          if (user.role === "ADMIN") {
            return audit(user);
          }
          return session(user);
        },
      },
    };
""")

PY_RESOLVER = textwrap.dedent("""
    def promote(ctx, user_id, role):
        require_admin(ctx)
        user = get(user_id)
        user.role = role
        return user


    def open_promote(user_id, role):
        user = get(user_id)
        user.role = role
        return user
""")


def test_parse_sdl_extracts_operations_and_flags():
    ops = {o.name: o for o in authz.parse_sdl(SDL)}
    assert set(ops) == {"me", "user", "users", "updateUser", "adminCreateUser", "setRole", "login", "deletePost"}
    assert ops["user"].object_scoped and not ops["users"].object_scoped
    assert ops["setRole"].sensitive and ops["deletePost"].sensitive and not ops["me"].sensitive
    assert ops["updateUser"].kind == "mutation" and ops["me"].kind == "query"


def test_matrix_covers_roles_ownership_and_anonymous():
    ops = authz.parse_sdl(SDL)
    rows = authz.build_matrix(ops, ["ADMIN", "USER"], ["user", "users"])
    keys = {(r["role"], r["operation"], r["ownership"]) for r in rows}
    assert ("ADMIN", "user", "own") in keys and ("USER", "user", "foreign") in keys
    assert ("ANONYMOUS", "user", "anonymous") in keys and ("ANONYMOUS", "users", "n/a") in keys
    assert all(r["expected"] is None for r in rows)


def test_skeletons_render_for_both_frameworks():
    rows = authz.build_matrix(authz.parse_sdl(SDL), ["ADMIN"], ["setRole"])
    bun = authz.render_bun_skeleton(rows)
    assert 'from "bun:test"' in bun and 'test.todo("ADMIN / own")' in bun
    py = authz.render_pytest_skeleton(rows)
    assert "pytest.mark.parametrize" in py and '("ADMIN", "setRole", "own")' in py
    compile(py, "skeleton", "exec")


def test_openapi_operations_parse():
    ops = authz.parse_openapi({"paths": {"/users/{id}": {"get": {"operationId": "getUser"}, "delete": {}}}})
    assert {o.name for o in ops} == {"getUser", "DELETE /users/{id}"}
    assert all(o.object_scoped for o in ops)


def test_role_paths_flag_weaker_write_paths(tmp_path):
    (tmp_path / "resolvers.ts").write_text(RESOLVERS)
    paths = {p["function"]: p for p in authz.scan_role_paths(tmp_path)}
    assert set(paths) == {"updateUser", "adminCreateUser", "setRole"}
    assert paths["updateUser"]["status"] == "ok"
    for name in ("adminCreateUser", "setRole"):
        assert paths[name]["status"] == "weaker" and paths[name]["weaker_than"] == ["updateUser"]
    assert "requireadmin" in paths["setRole"]["guards"]


def test_role_paths_python_and_unguarded(tmp_path):
    (tmp_path / "svc.py").write_text(PY_RESOLVER)
    paths = {p["function"]: p for p in authz.scan_role_paths(tmp_path)}
    assert paths["open_promote"]["status"] == "unguarded"
    assert paths["open_promote"]["guards"] == []
    assert paths["promote"]["status"] == "ok" and paths["promote"]["weaker_than"] == []


def test_role_paths_skip_tests_unless_requested(tmp_path):
    (tmp_path / "__tests__").mkdir()
    (tmp_path / "__tests__" / "a.ts").write_text(RESOLVERS)
    assert authz.scan_role_paths(tmp_path) == []
    assert len(authz.scan_role_paths(tmp_path, include_tests=True)) == 3


def test_test_db_guard_detection(tmp_path):
    (tmp_path / "setup.ts").write_text("export function assertFixtureDatabase(url: string) {}")
    assert authz.find_test_db_guard(tmp_path) == ["setup.ts"]
    assert authz.find_test_db_guard(tmp_path, "neverMatches") == []
    empty = tmp_path / "empty"
    empty.mkdir()
    assert authz.find_test_db_guard(empty) == []


COMPOSE = """
services:
  db:
    image: postgres:16
    ports: ["5432:5432"]
  cache:
    image: redis:7
    ports: ["6379:6379"]
  safe-cache:
    image: redis:7
    command: redis-server --requirepass secret
    ports: ["127.0.0.1:6380:6379"]
  worker:
    build: .
    ports: ["9000:9000"]
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    cap_add: [SYS_ADMIN]
    network_mode: host
  nginx:
    image: nginx
    user: "101"
    ports: ["80:80", "443:443"]
  loadgen:
    image: grafana/k6
    user: "1000"
    profiles: [loadtest]
"""


def _ids(findings):
    return [(f["id"], f["where"]) for f in findings]


def test_compose_review_flags_infrastructure_issues():
    findings = infra_review.review_compose(yaml.safe_load(COMPOSE))
    ids = _ids(findings)
    assert ("datastore-exposed", "db:5432") in ids
    assert ("datastore-exposed", "cache:6379") in ids
    assert ("redis-no-auth", "cache:6379") in ids
    assert not any(i[0] == "datastore-exposed" and i[1].startswith("safe-cache") for i in ids)
    assert not any(i[0] == "redis-no-auth" and i[1].startswith("safe-cache") for i in ids)
    assert ("service-exposed-all-interfaces", "worker:9000") in ids
    assert ("privileged-container", "worker") in ids
    assert ("docker-socket-mount", "worker") in ids
    assert ("dangerous-capability", "worker") in ids
    assert ("host-network", "worker") in ids
    assert ("missing-mem-limit", "loadgen") in ids
    assert not any(i[1].startswith("nginx") and i[0] != "container-root" for i in ids)
    assert ("container-root", "db") in ids and ("container-root", "nginx") not in ids


def test_compose_long_form_ports_and_limits():
    data = {"services": {"db": {"image": "postgres", "user": "70", "ports": [{"target": 5432, "published": 5432, "host_ip": "0.0.0.0"}],
                                 "profiles": ["loadtest"], "deploy": {"resources": {"limits": {"memory": "1g"}}}}}}
    findings = infra_review.review_compose(data)
    assert _ids(findings) == [("datastore-exposed", "db:5432")]
    loopback = {"services": {"db": {"image": "postgres", "user": "70", "ports": [{"target": 5432, "published": 5432, "host_ip": "127.0.0.1"}]}}}
    assert infra_review.review_compose(loopback) == []
    assert infra_review.parse_port("[::]:5432:5432/tcp") == ("[::]", 5432, 5432)
    assert infra_review.parse_port("8080") == ("", 0, 8080)
    assert infra_review.parse_port("bad:port") is None


BAD_NGINX = """
http {
  upstream api { server api-1:3000; server api-2:3000; }
  limit_req_zone $binary_remote_addr zone=z:10m rate=10r/s;
  server {
    listen 80;
    client_max_body_size 0;
    location / {
      proxy_pass http://api;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header Connection "upgrade";
    }
    location /docs { proxy_pass http://api; }
    location /metrics { allow 10.0.0.0/8; deny all; proxy_pass http://api; }
  }
}
"""

GOOD_NGINX = """
http {
  server_tokens off;
  resolver 127.0.0.11;
  upstream api { server 10.0.0.5:3000; }
  limit_req_zone $binary_remote_addr zone=z:10m rate=10r/s;
  server {
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Strict-Transport-Security "max-age=1" always;
    add_header Referrer-Policy no-referrer always;
    client_max_body_size 5m;
    location / {
      limit_req zone=z;
      proxy_pass http://api;
      proxy_set_header X-Forwarded-For $remote_addr;
    }
    location /docs { return 404; }
  }
}
"""


def test_nginx_review_flags_each_issue():
    ids = {f["id"] for f in infra_review.review_nginx(BAD_NGINX)}
    assert ids == {"server-tokens", "missing-security-headers", "xff-append", "no-rate-limit", "unlimited-body-size",
                   "upstream-static-dns", "connection-upgrade-hardcoded", "public-docs-endpoint"}
    docs = [f for f in infra_review.review_nginx(BAD_NGINX) if f["id"] == "public-docs-endpoint"]
    assert [d["where"] for d in docs] == ["location /docs"]


def test_nginx_review_accepts_hardened_config():
    assert infra_review.review_nginx(GOOD_NGINX) == []
    assert infra_review.review_nginx("client_max_body_size 200m;")[0]["id"] in {"server-tokens", "missing-security-headers", "no-rate-limit", "large-body-size"}


def _scaling_repo(tmp_path: Path, beats: int | None):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "chat-bus.ts").write_text("import { EventEmitter } from 'events';\nexport const chatBus = new EventEmitter();\n")
    (tmp_path / "src" / "jobs.ts").write_text("setInterval(() => sweep(), 60000);\n")
    (tmp_path / "src" / "cache.ts").write_text("export const userCache = new Map<string, User>();\nwriteFileSync('/tmp/x', 'y');\nconst sessions = new Map();\n")
    (tmp_path / "src" / "leader.ts").write_text("const leader = await tryLock('sweep');\nsetInterval(() => run(), 1000);\n")
    (tmp_path / "worker.py").write_text("from celery import Celery\napp = Celery('x')\napp.conf.beat_schedule = {'a': {}}\n")
    services = {"api": {"deploy": {"replicas": 4}}, "db": {"image": "postgres"}}
    if beats is not None:
        services["beat"] = {"command": "celery -A worker beat", "deploy": {"replicas": beats}}
    (tmp_path / "docker-compose.yml").write_text(yaml.safe_dump({"services": services}))
    (tmp_path / "nginx.conf").write_text("upstream api { server api-1:3000; }\nlocation / { proxy_set_header Connection \"upgrade\"; }\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.ts").write_text("export const testBus = new EventEmitter();\n")


def test_scaling_review_reports_reference_risks(tmp_path):
    _scaling_repo(tmp_path, beats=None)
    result = scaling.scan_repo(tmp_path, pool_size=21, max_connections=100)
    by_check = {}
    for f in result["findings"]:
        by_check.setdefault(f["check"], []).append(f)
    assert by_check["in-process-bus"][0]["file"] == "src/chat-bus.ts" and by_check["in-process-bus"][0]["severity"] == "high"
    assert [f["file"] for f in by_check["unled-scheduler"]] == ["src/jobs.ts"]
    assert by_check["local-cache"][0]["line"] == 1
    assert by_check["local-files"][0]["line"] == 2
    assert by_check["memory-state"][0]["line"] == 3
    assert by_check["celery-beat"][0]["message"].startswith("beat_schedule defined but no celery beat")
    assert {f["message"].split(":")[1].strip().split(" ")[0] for f in by_check["nginx-upstream"]} == {"api-1", "Connection"}
    assert not any(f["file"].startswith("tests/") for f in result["findings"])
    budget = result["db_connection_budget"]
    assert budget["status"] == "risk" and budget["used"] == 84 and budget["replicas"] == 4
    statuses = {c["id"]: c["status"] for c in result["checklist"]}
    assert statuses["celery-beat"] == "risk" and statuses["nginx-upstream"] == "risk"


def test_scaling_review_multiple_beats_and_budget_over_limit(tmp_path):
    _scaling_repo(tmp_path, beats=2)
    result = scaling.scan_repo(tmp_path, replicas=10, pool_size=20, max_connections=100, other_connections=5)
    beat = [f for f in result["findings"] if f["check"] == "celery-beat"]
    assert "2 celery beat instances" in beat[0]["message"]
    assert result["db_connection_budget"]["status"] == "risk" and result["db_connection_budget"]["used"] == 205
    assert [f for f in result["findings"] if f["check"] == "db-connection-budget"][0]["severity"] == "high"


def test_scaling_review_single_beat_is_clean_and_budget_not_assessed(tmp_path):
    _scaling_repo(tmp_path, beats=1)
    result = scaling.scan_repo(tmp_path)
    assert not [f for f in result["findings"] if f["check"] == "celery-beat"]
    assert result["db_connection_budget"]["status"] == "not_assessed"
    statuses = {c["id"]: c["status"] for c in result["checklist"]}
    assert statuses["celery-beat"] == "ok" and statuses["db-connection-budget"] == "not_assessed"


def test_scaling_review_pool_discovery_and_headroom(tmp_path):
    (tmp_path / "db.ts").write_text("export const pool = new Pool({ pool: { max: 18 } });\n")
    result = scaling.scan_repo(tmp_path, replicas=5, max_connections=100)
    budget = result["db_connection_budget"]
    assert budget["pool_size"] == 18 and budget["used"] == 90 and budget["status"] == "risk"
    assert [f for f in result["findings"] if f["check"] == "db-connection-budget"][0]["severity"] == "medium"
