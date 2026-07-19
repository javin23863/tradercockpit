from tools import dashboard, social_analytics


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
