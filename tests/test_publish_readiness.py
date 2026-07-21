import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import publish  # noqa: E402
import social_batch  # noqa: E402
import upload_tiktok  # noqa: E402
import upload_youtube  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_v2(folder, channel="youtube", status="approved", caption_mode=None):
    production = Path(folder)
    asset = production / "asset.mp4"
    claims = production / "claims.json"
    brief = production / "analysis.md"
    sources = production / "sources.md"
    script = production / "vo.txt"
    script_approval = production / "script-approval.json"
    production_approval = production / "production-approval.json"
    asset.write_bytes(b"approved asset")
    claims.write_text('{"verdict":"PASS","blocked":[],"checked_sections":1}', encoding="utf-8")
    brief.write_text("Bloomberg market framing with official evidence", encoding="utf-8")
    sources.write_text("Bloomberg framing receipt", encoding="utf-8")
    script.write_text("approved script", encoding="utf-8")
    script_approval.write_text(json.dumps({
        "schema": "tradercockpit-script-approval/v1",
        "status": "approved",
        "script": script.relative_to(ROOT).as_posix(),
        "scriptSha256": sha(script),
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-17T00:00:00Z",
    }), encoding="utf-8")
    production_approval.write_text(json.dumps({
        "schema": "tradercockpit-production-approval/v1",
        "status": "approved",
        "analysisBrief": brief.relative_to(ROOT).as_posix(),
        "analysisBriefSha256": sha(brief),
        "sourceReceipt": sources.relative_to(ROOT).as_posix(),
        "sourceReceiptSha256": sha(sources),
        "scriptApproval": script_approval.relative_to(ROOT).as_posix(),
        "scriptApprovalSha256": sha(script_approval),
        "framingSources": ["Bloomberg"],
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-17T00:05:00Z",
    }), encoding="utf-8")
    item = {
        "id": "release-item",
        "channel": channel,
        "status": status,
        "title": "Approved title",
        "copy": "Approved copy",
        "asset": asset.relative_to(ROOT).as_posix(),
        "claimsGate": claims.relative_to(ROOT).as_posix(),
        "productionApproval": production_approval.relative_to(ROOT).as_posix(),
        "captionMode": caption_mode or ("native" if channel == "youtube" else "burned"),
        "privacy": "private" if channel == "youtube" else "public",
        "publicationAuthorized": True,
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-17T00:10:00Z",
    }
    batch = {
        "schema": "social-batch/v2",
        "batchId": "release-test",
        "containsSyntheticMedia": True,
        "items": [item],
    }
    item["approvalSha256"] = social_batch.approval_fingerprint(
        batch["batchId"], item, batch["containsSyntheticMedia"], batch["schema"]
    )
    batch_path = production / "social-batch.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    return batch_path, batch


class FakeCredentials:
    def __init__(self, valid=True, expired=False, refresh_token="refresh", refresh_error=None):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refresh_error = refresh_error

    def refresh(self, request):
        if self.refresh_error:
            raise self.refresh_error
        self.valid = True

    def to_json(self):
        return "{}"


class CredentialsLoader:
    current = None

    @classmethod
    def from_authorized_user_file(cls, path, scopes):
        return cls.current


class FakeRequest:
    pass


class FakeCall:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class FakeChannels:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    def list(self, **kwargs):
        return FakeCall({"items": [{"id": self.channel_id}]})


class FakeYouTube:
    def __init__(self, channel_id=upload_youtube.EXPECTED_CHANNEL_ID):
        self.channel_id = channel_id

    def channels(self):
        return FakeChannels(self.channel_id)


class YouTubeReadinessTests(unittest.TestCase):
    def probe(self, token_exists, credentials=None, channel_id=upload_youtube.EXPECTED_CHANNEL_ID):
        with tempfile.TemporaryDirectory() as folder:
            token = Path(folder) / "token.json"
            if token_exists:
                token.write_text("{}", encoding="utf-8")
            CredentialsLoader.current = credentials
            google = (FakeRequest, CredentialsLoader, object(), lambda *args, **kwargs: FakeYouTube(channel_id))
            with patch.object(upload_youtube, "credential_path", return_value=token), patch.object(
                upload_youtube, "_google", return_value=google
            ):
                return upload_youtube.probe_auth()

    def test_absent_refreshable_revoked_and_valid_credentials_are_distinct(self):
        self.assertEqual("absent", self.probe(False)["status"])
        self.assertEqual(
            "refreshable-expired",
            self.probe(True, FakeCredentials(valid=False, expired=True))["status"],
        )
        self.assertEqual(
            "revoked",
            self.probe(True, FakeCredentials(valid=False, expired=True, refresh_error=RuntimeError("revoked")))["status"],
        )
        valid = self.probe(True, FakeCredentials())
        self.assertEqual("valid", valid["status"])
        self.assertEqual(upload_youtube.EXPECTED_CHANNEL_ID, valid["channelId"])

    def test_channel_mismatch_is_a_hard_failure(self):
        probe = self.probe(True, FakeCredentials(), channel_id="wrong-channel")
        self.assertEqual("channel-mismatch", probe["status"])
        self.assertFalse(probe["ready"])


class OtherReadinessTests(unittest.TestCase):
    def test_youtube_dependencies_are_required_before_auth_probe(self):
        with patch.object(publish, "module_available", return_value=False):
            self.assertEqual("dependency-missing", publish.youtube_readiness()["status"])

    def report(self, env, boto3):
        blocked = {"status": "absent", "ready": False}
        response = type("Response", (), {"json": lambda self: {"id": "verified"}})()
        with patch.dict(os.environ, env, clear=True), patch.object(
            publish, "youtube_readiness", return_value=blocked
        ), patch.object(publish, "tiktok_readiness", return_value=blocked), patch.object(
            publish, "module_available", side_effect=lambda name: boto3 if name == "boto3" else False
        ), patch.object(publish.requests, "get", return_value=response):
            return publish.readiness_report()

    def test_instagram_requires_dependencies_and_complete_staging_credentials(self):
        complete = {
            "META_APP_ID": "app",
            "META_APP_SECRET": "secret",
            "META_IG_USER_ID": "ig",
            "META_PAGE_TOKEN": "token",
            "B2_KEY_ID": "key",
            "B2_APP_KEY": "secret",
            "B2_BUCKET": "bucket",
            "B2_S3_ENDPOINT": "https://s3.us-west-004.backblazeb2.com",
        }
        self.assertFalse(self.report(complete, boto3=False)["instagram"]["ready"])
        self.assertTrue(self.report(complete, boto3=True)["instagram"]["ready"])
        del complete["B2_S3_ENDPOINT"]
        self.assertFalse(self.report(complete, boto3=True)["instagram"]["ready"])

    def test_meta_app_block_is_reported_and_fails_closed(self):
        complete = {
            "META_APP_ID": "app",
            "META_APP_SECRET": "secret",
            "META_PAGE_ID": "page",
            "META_IG_USER_ID": "ig",
            "META_PAGE_TOKEN": "token",
            "B2_KEY_ID": "key",
            "B2_APP_KEY": "secret",
            "B2_BUCKET": "bucket",
            "B2_S3_ENDPOINT": "https://s3.us-west-004.backblazeb2.com",
        }
        blocked = {"error": {"code": 200, "message": "API access blocked."}}
        response = type("Response", (), {"json": lambda self: blocked})()
        unavailable = {"status": "absent", "ready": False}
        with patch.dict(os.environ, complete, clear=True), patch.object(
            publish, "youtube_readiness", return_value=unavailable
        ), patch.object(publish, "tiktok_readiness", return_value=unavailable), patch.object(
            publish, "module_available", return_value=True
        ), patch.object(publish.requests, "get", return_value=response):
            report = publish.readiness_report()

        self.assertEqual("app-blocked", report["facebook"]["status"])
        self.assertFalse(report["facebook"]["ready"])
        self.assertEqual("app-blocked", report["instagram"]["status"])
        self.assertFalse(report["instagram"]["ready"])


class BatchAndPublicationTests(unittest.TestCase):
    def test_tiktok_official_api_smoke_writes_verified_batch_receipt_without_network(self):
        class Response:
            def __init__(self, payload=None, status_code=200):
                self.payload = payload or {}
                self.status_code = status_code

            def json(self):
                return self.payload

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise upload_tiktok.requests.HTTPError(f"HTTP {self.status_code}")

        def ok(data):
            return Response({"data": data, "error": {"code": "ok", "message": ""}})

        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            batch_path, _ = make_v2(folder, channel="tiktok")
            credentials = Path(folder) / "tiktok-oauth.json"
            credentials.write_text(json.dumps({
                "client_key": "client-key",
                "client_secret": "client-secret",
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_token_expires_at": 4_000_000_000,
                "refresh_token_expires_at": 4_100_000_000,
                "scope": "video.publish",
                "client_audit_status": "approved",
            }), encoding="utf-8")
            responses = [
                ok({
                    "creator_username": "thetradercockpit",
                    "privacy_level_options": ["PUBLIC_TO_EVERYONE"],
                    "comment_disabled": False,
                    "duet_disabled": False,
                    "stitch_disabled": False,
                }),
                ok({"publish_id": "publish-smoke", "upload_url": "https://upload.test/video"}),
                ok({
                    "status": "PUBLISH_COMPLETE",
                    "publicaly_available_post_id": ["post-smoke"],
                }),
            ]
            readiness = {
                channel: {"status": "absent", "ready": False}
                for channel in publish.LIVE_CHANNELS
            }
            readiness["tiktok"] = {"status": "valid", "ready": True}
            with patch.object(publish, "readiness_report", return_value=readiness), patch.object(
                upload_tiktok, "credential_path", return_value=credentials
            ), patch.object(
                upload_tiktok.requests, "post", side_effect=responses
            ) as post, patch.object(
                upload_tiktok.requests, "put", return_value=Response(status_code=201)
            ) as put:
                entry = publish.publish_batch_item(batch_path, "release-item", "tiktok")

            receipt = json.loads((Path(folder) / "publish_log.json").read_text(encoding="utf-8"))

        self.assertEqual("published", entry["status"])
        self.assertEqual("post-smoke", entry["platformId"])
        self.assertEqual(
            "https://www.tiktok.com/@thetradercockpit/video/post-smoke", entry["url"]
        )
        self.assertEqual("post-smoke", receipt["entries"][-1]["platformId"])
        self.assertEqual(3, post.call_count)
        put.assert_called_once()

    def test_v2_approval_binds_every_release_input_and_hash(self):
        mutations = {
            "title": lambda data, folder: data["items"][0].__setitem__("title", "changed"),
            "copy": lambda data, folder: data["items"][0].__setitem__("copy", "changed"),
            "caption": lambda data, folder: data["items"][0].__setitem__("captionMode", "none"),
            "privacy": lambda data, folder: data["items"][0].__setitem__("privacy", "unlisted"),
            "disclosure": lambda data, folder: data.__setitem__("containsSyntheticMedia", False),
            "publication authority": lambda data, folder: data["items"][0].__setitem__("publicationAuthorized", False),
            "asset": lambda data, folder: (Path(folder) / "asset.mp4").write_bytes(b"changed"),
            "claims": lambda data, folder: (Path(folder) / "claims.json").write_text(
                '{"verdict":"PASS","blocked":[],"checked_sections":2}', encoding="utf-8"
            ),
            "script": lambda data, folder: (Path(folder) / "vo.txt").write_text("changed", encoding="utf-8"),
            "production approval": lambda data, folder: (Path(folder) / "production-approval.json").write_text(
                (Path(folder) / "production-approval.json").read_text(encoding="utf-8") + " ", encoding="utf-8"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=ROOT) as folder:
                batch_path, data = make_v2(folder)
                mutate(data, folder)
                batch_path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    social_batch.load(batch_path)

    def test_v1_is_readable_but_never_live_publishable_and_video04_stays_rejected(self):
        video03 = ROOT / "productions" / "video-03-war-premium" / "social-batch.json"
        self.assertEqual("social-batch/v1", social_batch.load(video03)["schema"])
        video04 = ROOT / "productions" / "video-04-china-split" / "social-batch.json"
        data = social_batch.load(video04)
        self.assertEqual("rejected", data["items"][0]["status"])
        with self.assertRaisesRegex(ValueError, "historical evidence only"):
            publish.load_live_item(video04, data["items"][0]["id"])

    def test_live_rejects_drafts_rejections_burned_youtube_and_platform_mismatch(self):
        for status in ("draft", "rejected"):
            with self.subTest(status=status), tempfile.TemporaryDirectory(dir=ROOT) as folder:
                batch_path, _ = make_v2(folder, status=status)
                with self.assertRaisesRegex(ValueError, f"item status is {status}"):
                    publish.load_live_item(batch_path, "release-item")
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            batch_path, _ = make_v2(folder, caption_mode="burned")
            with self.assertRaisesRegex(ValueError, "caption-free master"):
                publish.load_live_item(batch_path, "release-item")
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            batch_path, _ = make_v2(folder)
            with self.assertRaisesRegex(ValueError, "platform mismatch"):
                publish.load_live_item(batch_path, "release-item", "facebook")

    def test_live_cli_requires_batch_item_and_rejects_arbitrary_file_title(self):
        with self.assertRaises(SystemExit):
            publish.main([])
        with self.assertRaises(SystemExit):
            publish.main(["video.mp4", "--title", "bypass"])

    def test_agent_environment_and_unverified_tiktok_fail_closed_without_upload(self):
        for channel, status in (("youtube", "absent"), ("tiktok", "private-only")):
            with self.subTest(channel=channel), tempfile.TemporaryDirectory(dir=ROOT) as folder:
                batch_path, _ = make_v2(folder, channel=channel)
                report = {
                    "youtube": {"status": "absent", "ready": False},
                    "instagram": {"status": "absent", "ready": False},
                    "facebook": {"status": "absent", "ready": False},
                    "tiktok": {"status": status, "ready": False},
                }
                with patch.object(publish, "readiness_report", return_value=report), patch.object(
                    publish, "dispatch_publish"
                ) as uploader:
                    with self.assertRaisesRegex(RuntimeError, status):
                        publish.publish_batch_item(batch_path, "release-item")
                    uploader.assert_not_called()
                entry = json.loads((Path(folder) / "publish_log.json").read_text(encoding="utf-8"))["entries"][-1]
                self.assertEqual("failed", entry["status"])
                self.assertIsNone(entry["platformId"])
                self.assertIsNone(entry["url"])

    def test_simulated_publisher_writes_verified_id_url_and_uploader_exit_stays_unverified(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            batch_path, data = make_v2(folder)
            result = {
                "status": "published",
                "id": "platform-123",
                "url": "https://example.test/platform-123",
                "platformResponse": {"readback": {"id": "platform-123"}},
            }
            report = publish.readiness_report()
            report["youtube"] = {"status": "valid", "ready": True}
            with patch.object(publish, "readiness_report", return_value=report), patch.object(
                publish, "dispatch_publish", return_value=result
            ):
                entry = publish.publish_batch_item(batch_path, "release-item")
            self.assertEqual(("published", "platform-123", result["url"]), (
                entry["status"], entry["platformId"], entry["url"]
            ))
            with patch.object(publish, "readiness_report", return_value=report), patch.object(
                publish, "dispatch_publish",
                return_value={"status": "uploaded-unverified", "id": None, "url": None},
            ), self.assertRaisesRegex(RuntimeError, "uploaded-unverified"):
                publish.publish_batch_item(batch_path, "release-item")
            unverified = json.loads((Path(folder) / "publish_log.json").read_text(encoding="utf-8"))["entries"][-1]
            self.assertEqual("uploaded-unverified", unverified["status"])
            self.assertIsNone(unverified["platformId"])
            self.assertIsNone(unverified["url"])


if __name__ == "__main__":
    unittest.main()
