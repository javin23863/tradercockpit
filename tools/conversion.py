#!/usr/bin/env python3
"""Render inert capture links and gate Buttondown signup behind --activate."""

import argparse
import copy
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    from tools.credential_custody import credential_path
    from tools.social_batch import REQUIRED_DISCLAIMER
except ModuleNotFoundError:  # direct `python tools/conversion.py` execution
    from credential_custody import credential_path
    from social_batch import REQUIRED_DISCLAIMER


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "social-ops" / "conversion-capture.v1.json"
PACKAGE_PATH = ROOT / "social-ops" / "conversion-publish-strings.json"
STATUS_PATH = ROOT / "social-ops" / "conversion-status.json"
BUTTONDOWN_SUBSCRIBERS_URL = "https://api.buttondown.com/v1/subscribers"
UTM_KEYS = {"utm_source", "utm_medium", "utm_campaign"}
SURFACES = {"video_description", "pinned_comment", "channel_link"}
STAGE_STATUSES = {
    "LIVE",
    "BUILT_BUT_OFF",
    "NOT_YET_EXISTING",
    "OUT_OF_SCOPE_NOT_BUILT",
    "STRUCTURALLY_UNAVAILABLE",
}


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def campaign_tag(episode_campaign_id, campaign_date):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", episode_campaign_id or ""):
        raise ValueError("episode_campaign_id must be a lowercase UTM slug")
    stamp = date.fromisoformat(campaign_date).strftime("%Y%m%d")
    suffix = f"_{stamp}"
    return episode_campaign_id if episode_campaign_id.endswith(suffix) else episode_campaign_id + suffix


def stamp_outbound_url(url, *, source, medium, episode_campaign_id, campaign_date):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError("outbound links must be absolute HTTPS URLs")
    for name, value in (("utm_source", source), ("utm_medium", medium)):
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value or ""):
            raise ValueError(f"{name} must be a lowercase UTM slug")
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key.lower() not in UTM_KEYS]
    query.extend([
        ("utm_source", source),
        ("utm_medium", medium),
        ("utm_campaign", campaign_tag(episode_campaign_id, campaign_date)),
    ])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def validate_config(value):
    if value.get("schema") != "conversion-capture/v1":
        raise ValueError("unsupported conversion capture schema")
    # Conservative operator-absent choice: checked-in configuration can describe activation,
    # but it may never turn activation on or select a paid/revenue surface.
    if value.get("status") != "BUILT_BUT_OFF" or value.get("activation", {}).get("enabled") is not False:
        raise ValueError("conversion capture must remain built-but-off")
    capture = value.get("capture", {})
    if capture.get("provider") != "buttondown" or capture.get("double_opt_in_required") is not True:
        raise ValueError("Buttondown with mandatory double opt-in is required")
    if capture.get("paid_offer_enabled") is not False:
        raise ValueError("paid offers must remain disabled")
    campaign = value.get("campaign", {})
    campaign_tag(campaign.get("episode_campaign_id"), campaign.get("campaign_date"))
    surfaces = value.get("surfaces", {})
    if set(surfaces) != SURFACES:
        raise ValueError("all and only the required conversion surfaces must be configured")
    for name, surface in surfaces.items():
        for field in ("utm_source", "utm_medium", "copy_template", "publish_mapping"):
            if not isinstance(surface.get(field), str) or not surface[field].strip():
                raise ValueError(f"{name}.{field} is required")
        if REQUIRED_DISCLAIMER not in surface["copy_template"]:
            raise ValueError(f"{name}.copy_template is missing the exact disclaimer")
    return value


def render_package(config):
    config = validate_config(config)
    campaign = config["campaign"]
    rendered = {}
    for name, surface in config["surfaces"].items():
        url = stamp_outbound_url(
            config["freebie"]["public_url"],
            source=surface["utm_source"],
            medium=surface["utm_medium"],
            episode_campaign_id=campaign["episode_campaign_id"],
            campaign_date=campaign["campaign_date"],
        )
        item = {
            "channel": surface["channel"],
            "publish_mapping": surface["publish_mapping"],
            "url": url,
            "copy": surface["copy_template"].replace("{capture_url}", url),
        }
        if surface.get("label"):
            item["label"] = surface["label"]
        rendered[name] = item
    return {
        "schema": "conversion-publish-strings/v1",
        "status": "BUILT_BUT_OFF",
        "campaign_tag": campaign_tag(campaign["episode_campaign_id"], campaign["campaign_date"]),
        "surfaces": rendered,
    }


def _signup_payload(request):
    email = str(request.get("email", "")).strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        raise ValueError("a valid email address is required")
    payload = {"email_address": email}
    for key in sorted(UTM_KEYS):
        value = request.get(key)
        if value:
            if not isinstance(value, str) or len(value) > 200:
                raise ValueError(f"{key} must be a short string")
            payload[key] = value
    # Omitting `type` is deliberate and mandatory: Buttondown's API then creates an
    # unactivated subscriber and sends its double-opt-in confirmation. Never add `regular`.
    assert "type" not in payload
    return payload


def _load_buttondown_api_key():
    path = credential_path("buttondown.env")
    values = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    key = values.get("BUTTONDOWN_API_KEY")
    if not key:
        raise RuntimeError("buttondown.env does not contain BUTTONDOWN_API_KEY")
    return key


def _live_buttondown_post(api_key, payload, *, activate=False):
    if activate is not True:
        raise RuntimeError("live Buttondown POST requires explicit activation")
    if "type" in payload:
        raise RuntimeError("Buttondown subscriber type is forbidden; double opt-in must remain enabled")
    # Importing the network client only after the activation guard makes the default path
    # physically incapable of opening the provider URL.
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    request = Request(
        BUTTONDOWN_SUBSCRIBERS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            status = response.status
            result = json.loads(response.read(65536).decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Buttondown rejected subscriber creation (HTTP {error.code})") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("Buttondown subscriber creation did not return a valid response") from error
    if status != 201 or result.get("type") != "unactivated":
        raise RuntimeError("Buttondown did not return the required unactivated double-opt-in state")
    return {
        "status": "PENDING_CONFIRMATION",
        "network_attempted": True,
        "provider_state": "unactivated",
        "subscriber_id": result.get("id"),
    }


def handle_signup(request, *, activate=False, credential_loader=None, live_sender=None):
    """Framework-neutral signup handler; no server is selected until an operator owns hosting."""
    payload = _signup_payload(request)
    if activate is not True:
        return {
            "status": "DRY_RUN",
            "network_attempted": False,
            "double_opt_in_required": True,
            "email": re.sub(r"(^.).*(@.*$)", r"\1…\2", payload["email_address"]),
            "attribution": {key: payload.get(key) for key in sorted(UTM_KEYS)},
        }
    loader = credential_loader or _load_buttondown_api_key
    sender = live_sender or _live_buttondown_post
    return sender(loader(), payload, activate=activate)


def validate_status(value):
    if value.get("schema") != "conversion-status/v1":
        raise ValueError("unsupported conversion status schema")
    stages = value.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("conversion status requires stages")
    ids = set()
    for stage in stages:
        if stage.get("id") in ids or stage.get("status") not in STAGE_STATUSES:
            raise ValueError("conversion stages must have unique ids and supported statuses")
        ids.add(stage.get("id"))
    for name, metric in value.get("metrics", {}).items():
        measured = metric.get("status") == "MEASURED"
        observed = metric.get("value")
        if observed is None:
            if measured:
                raise ValueError(f"{name}: a measured metric requires a value")
        elif isinstance(observed, bool) or not isinstance(observed, (int, float)) or observed < 0:
            raise ValueError(f"{name}: metric values must be null or non-negative numbers")
        elif not measured or not metric.get("measured_at"):
            raise ValueError(f"{name}: even zero requires MEASURED status and measured_at")
    return value


def selftest():
    html = (ROOT / "docs" / "strategy-claim-audit-checklist.html").read_text(encoding="utf-8")
    assert REQUIRED_DISCLAIMER in html
    assert BUTTONDOWN_SUBSCRIBERS_URL not in html and 'action="/api/signup"' in html
    assert 'data-activation="off"' in html and 'onsubmit="return false"' in html
    config = validate_config(_load_json(CONFIG_PATH))
    rendered = render_package(config)
    assert rendered == _load_json(PACKAGE_PATH)
    campaign = config["campaign"]
    for name, surface in rendered["surfaces"].items():
        stamped = surface["url"]
        source = config["surfaces"][name]
        assert stamped == stamp_outbound_url(
            stamped,
            source=source["utm_source"],
            medium=source["utm_medium"],
            episode_campaign_id=campaign["episode_campaign_id"],
            campaign_date=campaign["campaign_date"],
        )
        assert all(stamped.count(f"{key}=") == 1 for key in UTM_KEYS)

    parser = build_parser()
    assert parser.parse_args(["signup", "--email", "test@example.com"]).activate is False
    bomb = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("dry run touched live dependency"))
    dry = handle_signup({"email": "test@example.com"}, credential_loader=bomb, live_sender=bomb)
    assert dry["network_attempted"] is False and dry["status"] == "DRY_RUN"
    seen = {}

    def fake_sender(key, payload, *, activate=False):
        seen.update(key=key, payload=payload, activate=activate)
        return {"status": "PENDING_CONFIRMATION", "network_attempted": True,
                "provider_state": "unactivated", "subscriber_id": "local-selftest"}

    live = handle_signup(
        {"email": "test@example.com", "utm_source": "youtube"},
        activate=True,
        credential_loader=lambda: "local-fake-key",
        live_sender=fake_sender,
    )
    assert seen["activate"] is True and "type" not in seen["payload"]
    assert live["provider_state"] == "unactivated"

    status = validate_status(_load_json(STATUS_PATH))
    assert all(metric["value"] is None for metric in status["metrics"].values())
    broken = copy.deepcopy(status)
    broken["metrics"]["outbound_link_clicks"]["value"] = 0
    try:
        validate_status(broken)
        raise AssertionError("unmeasured zero should fail")
    except ValueError:
        pass
    print("conversion self-test: freebie 3/3; UTM 3/3; activation gate 5/5; status 3/3 PASS")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("render", help="print the inert publish-string package")
    signup = subparsers.add_parser("signup", help="validate a signup; dry-run unless --activate")
    signup.add_argument("--email", required=True)
    signup.add_argument("--utm-source")
    signup.add_argument("--utm-medium")
    signup.add_argument("--utm-campaign")
    signup.add_argument("--activate", action="store_true", help="allow one live Buttondown POST")
    subparsers.add_parser("check-status", help="validate null-vs-zero status semantics")
    subparsers.add_parser("selftest", help="run local assert-based checks")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "render":
        print(json.dumps(render_package(_load_json(CONFIG_PATH)), indent=2, ensure_ascii=False))
    elif args.command == "signup":
        result = handle_signup({
            "email": args.email,
            "utm_source": args.utm_source,
            "utm_medium": args.utm_medium,
            "utm_campaign": args.utm_campaign,
        }, activate=args.activate)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "check-status":
        validate_status(_load_json(STATUS_PATH))
        print("conversion status: PASS")
    else:
        selftest()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"BLOCK: {error}") from error
