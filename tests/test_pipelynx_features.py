"""
Pipelynx backend tests for new feature batch:
  - GET /api/v1/runs/live  (in_flight + recent + sources aggregation)
  - GET /api/v1/pipelines/integrations/{id}/setup-guide (per platform; public webhook URL)
  - POST /api/v1/pipelines/integrations/{id}/sync (pull vs webhook handling)
  - DELETE /api/v1/pipelines/integrations/{id}
  - Existing regressions: login, runs list, metrics, alerts test (email — single shot)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api/v1"
PUBLIC_HOST = BASE_URL.replace("https://", "").replace("http://", "")

ADMIN_EMAIL = "admin@sparkcurv.com"
ADMIN_PASSWORD = "Aiden@1996"


@pytest.fixture(scope="session")
def auth_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token") or (data.get("data") or {}).get("access_token")
    assert token, f"no token in response: {data}"
    return token


@pytest.fixture(scope="session")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})
    return s


# ---------- Auth regression ----------
class TestAuthRegression:
    def test_login_ok(self, auth_token):
        assert isinstance(auth_token, str) and len(auth_token) > 10


# ---------- Runs / Live ----------
class TestRunsLive:
    def test_runs_list_ok(self, client):
        r = client.get(f"{API}/runs/", timeout=20)
        assert r.status_code == 200, r.text

    def test_live_endpoint_shape(self, client):
        r = client.get(f"{API}/runs/live", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("in_flight", "recent", "sources", "as_of"):
            assert k in data, f"missing {k} in {list(data.keys())}"
        assert isinstance(data["in_flight"], list)
        assert isinstance(data["recent"], list)
        assert len(data["recent"]) <= 20
        assert isinstance(data["sources"], (list, dict))
        # sources aggregation should contain counter fields per platform
        srcs = data["sources"]
        if isinstance(srcs, dict):
            iterable = srcs.values()
        else:
            iterable = srcs
        for entry in iterable:
            for f in ("running", "queued", "failure", "success", "total"):
                assert f in entry, f"sources entry missing '{f}': {entry}"


# ---------- Integrations: create/setup-guide/sync/delete ----------
class TestIntegrationsLifecycle:
    @pytest.fixture(scope="class")
    def webhook_integration(self, client):
        body = {
            "type": "github",
            "name": "TEST_webhook_github",
            "config": {"connection_mode": "webhook", "webhook_secret": "TEST_secret"},
        }
        r = client.post(f"{API}/pipelines/integrations", json=body, timeout=20)
        assert r.status_code in (200, 201), r.text
        integ = r.json()
        assert "id" in integ
        yield integ
        client.delete(f"{API}/pipelines/integrations/{integ['id']}", timeout=20)

    @pytest.fixture(scope="class")
    def pull_integration(self, client):
        body = {
            "type": "github",
            "name": "TEST_pull_github",
            "config": {
                "connection_mode": "pull",
                "api_token": "fake_bad_token",
                "repositories": ["octocat/Hello-World"],
            },
        }
        r = client.post(f"{API}/pipelines/integrations", json=body, timeout=20)
        assert r.status_code in (200, 201), r.text
        integ = r.json()
        yield integ
        client.delete(f"{API}/pipelines/integrations/{integ['id']}", timeout=20)

    def test_create_pull_persists_config(self, client, pull_integration):
        r = client.get(f"{API}/pipelines/integrations", timeout=20)
        assert r.status_code == 200
        items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        ids = [i.get("id") for i in items]
        assert pull_integration["id"] in ids
        # find ours and verify config persisted
        ours = next(i for i in items if i.get("id") == pull_integration["id"])
        cfg = ours.get("config") or {}
        assert cfg.get("connection_mode") == "pull"
        assert "octocat/Hello-World" in (cfg.get("repositories") or [])

    @pytest.mark.parametrize("platform", ["github", "gitlab", "jenkins", "bitbucket", "circleci", "argocd", "aws"])
    def test_setup_guide_all_platforms(self, client, platform):
        # create a throw-away integration of the platform
        r = client.post(
            f"{API}/pipelines/integrations",
            json={"type": platform, "name": f"TEST_guide_{platform}", "config": {"connection_mode": "webhook"}},
            timeout=20,
        )
        assert r.status_code in (200, 201), r.text
        iid = r.json()["id"]
        try:
            gr = client.get(f"{API}/pipelines/integrations/{iid}/setup-guide", timeout=20)
            assert gr.status_code == 200, gr.text
            guide = gr.json()
            for k in ("mode", "title", "summary", "steps", "integration"):
                assert k in guide, f"{platform}: missing {k}"
            assert isinstance(guide["steps"], list) and len(guide["steps"]) >= 1
            # collect all code values
            codes = " ".join((s.get("code") or "") for s in guide["steps"])
            assert "localhost" not in codes, f"{platform}: webhook code contains localhost: {codes}"
            assert "<your-pipelynx-domain>" not in codes, f"{platform}: placeholder host still in code"
            assert PUBLIC_HOST in codes, f"{platform}: public host {PUBLIC_HOST} not in code: {codes}"
            assert f"/api/v1/webhooks/{platform}" in codes, f"{platform}: webhook path missing"
        finally:
            client.delete(f"{API}/pipelines/integrations/{iid}", timeout=20)

    def test_sync_webhook_mode_returns_400(self, client, webhook_integration):
        r = client.post(f"{API}/pipelines/integrations/{webhook_integration['id']}/sync", timeout=20)
        assert r.status_code == 400, f"expected 400 for webhook sync, got {r.status_code}: {r.text}"

    def test_sync_pull_mode_bad_token_graceful(self, client, pull_integration):
        r = client.post(f"{API}/pipelines/integrations/{pull_integration['id']}/sync", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True, data
        assert data.get("ingested", -1) == 0, data

    def test_delete_integration_then_404(self, client):
        # create
        r = client.post(
            f"{API}/pipelines/integrations",
            json={"type": "github", "name": "TEST_to_delete", "config": {"connection_mode": "webhook"}},
            timeout=20,
        )
        assert r.status_code in (200, 201)
        iid = r.json()["id"]
        # delete
        d = client.delete(f"{API}/pipelines/integrations/{iid}", timeout=20)
        assert d.status_code == 200, d.text
        # subsequent get setup-guide should be 404
        g = client.get(f"{API}/pipelines/integrations/{iid}/setup-guide", timeout=20)
        assert g.status_code == 404


# ---------- Metrics / Alerts regression ----------
class TestRegression:
    def test_metrics_summary(self, client):
        r = client.get(f"{API}/metrics/summary", timeout=20)
        assert r.status_code == 200, r.text

    def test_alerts_email_single(self, client):
        # single test — do NOT spam
        r = client.post(
            f"{API}/alerts/test",
            json={"channel": "email", "config": {"recipients": ["kesari4416@gmail.com"]}},
            timeout=45,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True, r.text
