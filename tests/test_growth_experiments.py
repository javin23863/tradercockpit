import copy
import csv
import json
from pathlib import Path

import pytest

from tools.dashboard import render_growth
from tools.growth_experiments import load_growth_summary


METRIC_FIELDS = [
    "date", "batch_id", "item_id", "channel", "public_url", "published_at_et",
    "on_time", "claims_gate", "corrections", "impressions", "views", "ctr_percent",
    "three_second_hold_percent", "completion_percent", "average_percentage_viewed",
    "replays", "shares", "saves", "qualified_comments", "landing_visits", "cta_clicks",
    "confirmed_signups", "approval_to_publish_minutes", "lesson",
]


def metric_row(item_id="item-1", **changes):
    row = {field: "" for field in METRIC_FIELDS}
    row.update({
        "batch_id": "batch-1",
        "item_id": item_id,
        "channel": "tiktok",
        "claims_gate": "PASS",
        "corrections": "0",
        "views": "100",
        "completion_percent": "40",
        "shares": "2",
        "saves": "1",
        "landing_visits": "10",
        "cta_clicks": "1",
        "confirmed_signups": "1",
    })
    row.update({key: str(value) for key, value in changes.items()})
    return row


def make_workspace(tmp_path, rows=None):
    social_ops = tmp_path / "social-ops"
    social_ops.mkdir(parents=True)
    (social_ops / "baseline.json").write_text('{"reviewed": true}', encoding="utf-8")
    batch = {
        "schema": "social-batch/v1",
        "batchId": "batch-1",
        "items": [
            {"id": "item-1", "channel": "tiktok"},
            {"id": "item-2", "channel": "tiktok"},
        ],
    }
    (social_ops / "batch.json").write_text(json.dumps(batch), encoding="utf-8")
    metrics_path = social_ops / "metrics.csv"
    with metrics_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        writer.writerows(rows if rows is not None else [metric_row()])
    return social_ops / "growth.json", metrics_path


def base_manifest():
    return {
        "schema": "tradercockpit-growth-experiments/v1",
        "updatedAt": "2026-07-16T12:00:00+07:00",
        "paidActivation": "disabled",
        "libraries": {
            "audiences": [{
                "id": "audience/test", "state": "active", "label": "Audience", "description": "Audience description",
            }],
            "angles": [{
                "id": "angle/test", "state": "active", "label": "Angle", "description": "Angle description",
            }],
            "hooks": [
                {"id": "hook/a", "state": "active", "label": "Hook A", "description": "First hook"},
                {"id": "hook/b", "state": "active", "label": "Hook B", "description": "Second hook"},
            ],
            "formats": [{
                "id": "format/test", "state": "active", "label": "Format", "description": "Format description",
            }],
            "offers": [
                {"id": "offer/test", "state": "active", "label": "Offer", "description": "Offer description"},
                {
                    "id": "offer/blocked", "state": "blocked", "label": "Blocked offer",
                    "description": "Future capability", "unlock": "Verified consumer capability",
                },
            ],
        },
        "experiments": [base_experiment()],
    }


def base_experiment():
    return {
        "id": "exp-test-1",
        "lane": "new",
        "state": "running",
        "surface": "tiktok",
        "hypothesis": "A focused hook improves completion.",
        "assembly": {
            "audience": "audience/test",
            "angle": "angle/test",
            "hook": "hook/a",
            "format": "format/test",
            "offer": "offer/test",
        },
        "changedComponent": "hook",
        "comparison": "baseline",
        "observations": [{"batch": "social-ops/batch.json", "itemId": "item-1"}],
        "metrics": {
            "primary": "completion_percent",
            "secondary": ["shares_per_1000_views", "cta_click_rate_percent"],
            "guardrails": ["claims_gate_pass", "corrections_zero"],
        },
        "decisionRule": {
            "status": "locked",
            "aggregation": "median",
            "minimumObservations": 1,
            "killBelow": 20,
            "reuseAtOrAbove": 50,
            "baselineReceipt": "social-ops/baseline.json",
        },
        "decision": {"verdict": "pending", "reason": None, "decidedAt": None},
        "blockers": [],
    }


def summarize(tmp_path, manifest=None, rows=None):
    manifest_path, metrics_path = make_workspace(tmp_path, rows)
    manifest_path.write_text(json.dumps(manifest or base_manifest()), encoding="utf-8")
    return load_growth_summary(manifest_path, metrics_path, root=tmp_path)


def test_seed_manifest_is_valid_and_deterministic():
    first = load_growth_summary()
    second = load_growth_summary()
    assert first == second
    assert first["valid"] is True
    assert first["paidActivation"] == "disabled"
    assert [item["id"] for item in first["experiments"]] == ["exp-2026-001", "exp-2026-002"]
    assert first["experiments"][0]["advisory"]["verdict"] == "insufficient_evidence"
    assert first["experiments"][1]["advisory"]["verdict"] == "blocked"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["libraries"]["audiences"].append(copy.deepcopy(data["libraries"]["audiences"][0])), "duplicate library id"),
        (lambda data: data["experiments"].append(copy.deepcopy(data["experiments"][0])), "duplicate experiment id"),
        (lambda data: data["libraries"]["hooks"][0].update(id="angle/wrong"), "must start with hook/"),
        (lambda data: data["experiments"][0].update(id="test-1"), "must start with exp-"),
        (lambda data: data["experiments"][0]["assembly"].update(hook="hook/missing"), "unknown hook"),
        (lambda data: data["experiments"][0]["assembly"].update(offer="offer/blocked"), "must remain blocked"),
        (lambda data: data["experiments"][0].update(state="measured", observations=[]), "requires observations"),
    ],
)
def test_rejects_identity_reference_and_state_errors(tmp_path, mutate, message):
    manifest = base_manifest()
    mutate(manifest)
    with pytest.raises(ValueError, match=message):
        summarize(tmp_path, manifest)


def test_comparison_changes_exactly_the_declared_component(tmp_path):
    manifest = base_manifest()
    candidate = copy.deepcopy(manifest["experiments"][0])
    candidate.update(id="exp-test-2", comparison="exp-test-1")
    candidate["assembly"].update(hook="hook/b", format="format/other")
    manifest["libraries"]["formats"].append({
        "id": "format/other", "state": "active", "label": "Other", "description": "Other format",
    })
    manifest["experiments"].append(candidate)
    with pytest.raises(ValueError, match="must change exactly hook"):
        summarize(tmp_path, manifest)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"batch": "../outside.json"}, "must stay inside TraderCockpit"),
        ({"batch": "C:\\outside.json"}, "must be repo-relative"),
        ({"itemId": "missing"}, "must identify one batch item"),
    ],
)
def test_rejects_unsafe_or_missing_observations(tmp_path, change, message):
    manifest = base_manifest()
    manifest["experiments"][0]["observations"][0].update(change)
    with pytest.raises(ValueError, match=message):
        summarize(tmp_path, manifest)


def test_rejects_batch_and_metric_channel_mismatches(tmp_path):
    manifest_path, metrics_path = make_workspace(tmp_path, [metric_row(channel="youtube")])
    manifest_path.write_text(json.dumps(base_manifest()), encoding="utf-8")
    with pytest.raises(ValueError, match="metrics.csv channel must match"):
        load_growth_summary(manifest_path, metrics_path, root=tmp_path)

    batch_path = tmp_path / "social-ops" / "batch.json"
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    batch["items"][0]["channel"] = "youtube"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    with pytest.raises(ValueError, match="itemId channel must match"):
        load_growth_summary(manifest_path, metrics_path, root=tmp_path)


def test_nulls_and_derived_rates_preserve_unknown_denominators(tmp_path):
    manifest = base_manifest()
    experiment = manifest["experiments"][0]
    experiment["metrics"].update(
        primary="shares_per_1000_views",
        secondary=["cta_click_rate_percent", "confirmed_signup_rate_percent"],
    )
    missing = summarize(tmp_path / "missing", manifest, [metric_row(views=0, landing_visits="")])
    observation = missing["experiments"][0]["observations"][0]
    assert observation["metrics"] == {
        "shares_per_1000_views": None,
        "cta_click_rate_percent": None,
        "confirmed_signup_rate_percent": None,
    }
    assert missing["experiments"][0]["primaryMedian"] is None
    assert missing["experiments"][0]["advisory"]["verdict"] == "insufficient_evidence"

    measured = summarize(
        tmp_path / "measured",
        manifest,
        [metric_row(views=200, shares=4, landing_visits=20, cta_clicks=2, confirmed_signups=1)],
    )
    values = measured["experiments"][0]["observations"][0]["metrics"]
    assert values == {
        "shares_per_1000_views": 20,
        "cta_click_rate_percent": 10,
        "confirmed_signup_rate_percent": 5,
    }

    with pytest.raises(ValueError, match="must be finite"):
        summarize(tmp_path / "not-finite", base_manifest(), [metric_row(completion_percent="NaN")])
    with pytest.raises(ValueError, match="must not be negative"):
        summarize(tmp_path / "negative", base_manifest(), [metric_row(completion_percent=-1)])
    with pytest.raises(ValueError, match="must not exceed 100"):
        summarize(tmp_path / "over-100", base_manifest(), [metric_row(completion_percent=999)])
    with pytest.raises(ValueError, match="cta_click_rate_percent must not exceed 100"):
        summarize(tmp_path / "derived-over-100", base_manifest(),
                  [metric_row(cta_clicks=50, landing_visits=10)])


def test_pending_baseline_and_too_few_observations_are_insufficient(tmp_path):
    manifest = base_manifest()
    experiment = manifest["experiments"][0]
    experiment.update(state="proposed", observations=[])
    experiment["decisionRule"] = {
        "status": "pending_baseline", "aggregation": "median", "minimumObservations": None,
        "killBelow": None, "reuseAtOrAbove": None, "baselineReceipt": None,
    }
    summary = summarize(tmp_path / "pending", manifest)
    assert summary["experiments"][0]["advisory"]["verdict"] == "insufficient_evidence"

    manifest = base_manifest()
    manifest["experiments"][0]["decisionRule"]["minimumObservations"] = 2
    summary = summarize(tmp_path / "count", manifest)
    assert summary["experiments"][0]["advisory"]["verdict"] == "insufficient_evidence"


@pytest.mark.parametrize(("value", "verdict"), [(10, "kill"), (30, "iterate"), (50, "reuse")])
def test_advisory_threshold_branches(tmp_path, value, verdict):
    summary = summarize(tmp_path, rows=[metric_row(completion_percent=value)])
    experiment = summary["experiments"][0]
    assert experiment["primaryMedian"] == value
    assert experiment["advisory"]["verdict"] == verdict


@pytest.mark.parametrize("guardrail_change", [{"claims_gate": "FAIL"}, {"corrections": 1}])
def test_hard_guardrails_force_kill(tmp_path, guardrail_change):
    summary = summarize(tmp_path, rows=[metric_row(completion_percent=75, **guardrail_change)])
    assert summary["experiments"][0]["advisory"]["verdict"] == "kill"


@pytest.mark.parametrize("guardrail_change", [{"claims_gate": ""}, {"corrections": ""}])
def test_unknown_guardrails_are_insufficient_evidence(tmp_path, guardrail_change):
    summary = summarize(tmp_path, rows=[metric_row(completion_percent=75, **guardrail_change)])
    assert summary["experiments"][0]["advisory"]["verdict"] == "insufficient_evidence"


def test_operator_override_requires_reason_and_cannot_override_guardrail_to_reuse(tmp_path):
    manifest = base_manifest()
    experiment = manifest["experiments"][0]
    experiment["state"] = "decided"
    experiment["decision"] = {
        "verdict": "iterate",
        "reason": "The hook won, but qualitative comments show the consequence needs clearer sourcing.",
        "decidedAt": "2026-07-16T18:00:00+07:00",
    }
    summary = summarize(tmp_path / "override", manifest, [metric_row(completion_percent=75)])
    assert summary["experiments"][0]["advisory"]["verdict"] == "reuse"
    assert summary["experiments"][0]["decision"]["verdict"] == "iterate"

    experiment["decision"] = {"verdict": "reuse", "reason": "Override", "decidedAt": "2026-07-16T18:00:00+07:00"}
    with pytest.raises(ValueError, match="cannot reuse after a hard guardrail failure"):
        summarize(tmp_path / "guardrail", manifest, [metric_row(completion_percent=75, claims_gate="FAIL")])


def test_dashboard_escapes_growth_text_and_survives_invalid_manifest():
    valid = {
        "valid": True,
        "updatedAt": '<script>alert("date")</script>',
        "paidActivation": "disabled",
        "libraryCounts": {"hooks": {"active": 1, "hypothesis": 0, "blocked": 0}},
        "experiments": [{
            "id": "exp-x", "surface": "tiktok", "state": "proposed",
            "hypothesis": '<img src=x onerror="alert(1)">', "assembly": {"hook": "hook/<bad>"},
            "observationCount": 0, "primaryMetric": "completion_percent", "primaryMedian": None,
            "advisory": {"verdict": "insufficient_evidence", "reason": "<unsafe>"},
            "decision": {"verdict": "pending"}, "blockers": ["<blocked>"],
        }],
    }
    rendered = render_growth(valid)
    assert "<script>" not in rendered
    assert "<img " not in rendered
    assert "&lt;unsafe&gt;" in rendered
    assert "completion_percent: —" in rendered

    blocked = render_growth({"valid": False, "error": "<bad manifest>"})
    assert "Growth contract invalid" in blocked
    assert "&lt;bad manifest&gt;" in blocked
    assert "growth_experiments.py validate" in blocked
