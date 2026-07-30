import sys
import types

import pytest

from tools import dashboard, social_analytics


class _Request:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.result


class _Endpoint:
    def __init__(self, requests):
        self.requests = iter(requests)

    def list(self, **_kwargs):
        return next(self.requests)


class _YouTube:
    def __init__(self, search_requests):
        self.search_endpoint = _Endpoint(search_requests)

    def search(self):
        return self.search_endpoint

    def videos(self):
        return _Endpoint([_Request({"items": []})])

    def channels(self):
        return _Endpoint([_Request({"items": []})])


def _fake_google(monkeypatch, youtube):
    discovery = types.ModuleType("googleapiclient.discovery")
    discovery.build = lambda *_args, **_kwargs: youtube
    package = types.ModuleType("googleapiclient")
    package.discovery = discovery
    monkeypatch.setitem(sys.modules, "googleapiclient", package)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", discovery)


def test_demand_queries_support_episode_specific_phrases():
    assert social_analytics.demand_queries(
        [" monte carlo backtest ", "monte carlo backtest", "exit setting sensitivity"]
    ) == ("monte carlo backtest", "exit setting sensitivity")


def test_hotdog_custom_queries_complete_and_write_requested_output(monkeypatch, tmp_path):
    output = tmp_path / "episode-demand.json"
    youtube = _YouTube([_Request({"items": []}), _Request({"items": []})])
    _fake_google(monkeypatch, youtube)
    refresh = []
    monkeypatch.setattr(
        social_analytics,
        "youtube_credentials",
        lambda allow_refresh: refresh.append(allow_refresh) or object(),
    )

    payload = social_analytics.hotdog(["one", "two"], output)

    assert payload["status"] == "ok"
    assert len(payload["queryCoverage"]) == 2
    assert output.is_file()
    assert not refresh[0]


def test_hotdog_default_query_set_remains_complete(monkeypatch, tmp_path):
    output = tmp_path / "default-demand.json"
    youtube = _YouTube([_Request({"items": []}) for _ in social_analytics.FAILURE_PHRASES])
    _fake_google(monkeypatch, youtube)
    monkeypatch.setattr(social_analytics, "youtube_credentials", lambda allow_refresh: object())

    payload = social_analytics.hotdog(None, output)

    assert payload["status"] == "ok"
    assert len(payload["queryCoverage"]) == len(social_analytics.FAILURE_PHRASES)


@pytest.mark.parametrize("requests", [
    [_Request({"items": []}), _Request(error=RuntimeError("partial"))],
    [_Request(error=RuntimeError("first")), _Request(error=RuntimeError("second"))],
])
def test_hotdog_failed_query_sets_leave_output_untouched(monkeypatch, tmp_path, requests):
    output = tmp_path / "episode-demand.json"
    output.write_text("known-good", encoding="utf-8")
    _fake_google(monkeypatch, _YouTube(requests))
    monkeypatch.setattr(social_analytics, "youtube_credentials", lambda allow_refresh: object())

    with pytest.raises(SystemExit, match="output left untouched"):
        social_analytics.hotdog(["one", "two"], output)

    assert output.read_text(encoding="utf-8") == "known-good"


def test_hotdog_expired_credentials_leave_output_untouched(monkeypatch, tmp_path):
    output = tmp_path / "episode-demand.json"
    output.write_text("known-good", encoding="utf-8")
    _fake_google(monkeypatch, _YouTube([]))

    def expired(allow_refresh):
        assert allow_refresh is False
        raise SystemExit("expired")

    monkeypatch.setattr(social_analytics, "youtube_credentials", expired)

    with pytest.raises(SystemExit, match="expired"):
        social_analytics.hotdog(["one"], output)

    assert output.read_text(encoding="utf-8") == "known-good"


def test_safe_error_redacts_access_token():
    value = social_analytics.safe_error("boom https://example.test?a=1&access_token=secret&x=2")
    assert "secret" not in value
    assert "<redacted>" in value


def test_source_total_ignores_missing_and_non_numeric_values():
    source = {"posts": [{"views": 12}, {"views": None}, {}, {"views": 3.5}]}
    assert social_analytics.source_total(source) == 15


def test_decisions_surface_partial_youtube_and_baseline():
    sources = {
        "youtube": {"status": "partial", "analyticsAction": "https://example.test/enable"},
        "facebook": {"status": "ready", "posts": []},
        "instagram": {"status": "ready", "posts": []},
        "tiktok": {"status": "ready", "posts": []},
    }
    titles = [item["title"] for item in social_analytics.make_decisions(sources, has_prior=False)]
    assert "Enable YouTube retention reporting" in titles
    assert "Treat this as baseline week" in titles


def test_dashboard_escapes_source_content():
    snapshot = {
        "generatedAt": "2026-07-16T00:00:00Z",
        "window": {"start": "2026-07-09", "end": "2026-07-15"},
        "rollup": {"connectedSources": 1, "tiktokObservedViews": 1},
        "sources": {
            "youtube": {"status": "partial", "posts": [], "daily": []},
            "facebook": {"status": "missing_credentials", "posts": []},
            "instagram": {"status": "missing_credentials", "posts": []},
            "tiktok": {"status": "ready", "posts": [{"title": "<script>x</script>", "views": 1}]},
        },
        "decisions": [],
        "caveats": [],
    }
    page = dashboard.render_social(snapshot)
    assert "<script>x</script>" not in page
    assert "&lt;script&gt;x&lt;/script&gt;" in page


def test_dashboard_surfaces_ready_youtube_audience_quality():
    snapshot = {
        "generatedAt": "2026-07-16T00:00:00Z",
        "window": {"start": "2026-07-09", "end": "2026-07-15"},
        "rollup": {"connectedSources": 4, "youtubeWeeklyViews": 97},
        "sources": {
            "youtube": {
                "status": "ready",
                "posts": [],
                "daily": [],
                "weekly": {
                    "estimatedMinutesWatched": 28,
                    "averageViewDuration": 38,
                    "averageViewPercentage": 38.15,
                    "subscribersGained": 1,
                    "subscribersLost": 0,
                    "likes": 2,
                    "comments": 3,
                    "shares": 4,
                },
            },
            "facebook": {"status": "ready", "posts": []},
            "instagram": {"status": "ready", "posts": []},
            "tiktok": {"status": "ready", "posts": []},
        },
        "decisions": [],
        "caveats": [],
    }

    page = dashboard.render_social(snapshot)

    assert "YouTube audience quality" in page
    assert "28" in page and "estimated watch minutes" in page
    assert "38.15%" in page and "average percentage viewed" in page
    assert "9" in page and "likes + comments + shares" in page
    assert "+1 net subscribers" in page
