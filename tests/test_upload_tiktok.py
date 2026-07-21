import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import upload_tiktok  # noqa: E402


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self.payload = payload or {}
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise upload_tiktok.requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, post_responses, put_responses=()):
        self.post_responses = list(post_responses)
        self.put_responses = list(put_responses)
        self.posts = []
        self.puts = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return self.post_responses.pop(0)

    def put(self, url, **kwargs):
        self.puts.append((url, kwargs))
        return self.put_responses.pop(0)


def ok(data):
    return FakeResponse({"data": data, "error": {"code": "ok", "message": ""}})


def creator(*privacy):
    return ok({
        "creator_username": "thetradercockpit",
        "privacy_level_options": list(privacy),
        "comment_disabled": False,
        "duet_disabled": False,
        "stitch_disabled": False,
        "max_video_post_duration_sec": 300,
    })


class TikTokOfficialApiTests(unittest.TestCase):
    def write_credentials(self, folder, **overrides):
        values = {
            "client_key": "client-key",
            "client_secret": "client-secret",
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "access_token_expires_at": 2_000_000_000,
            "refresh_token_expires_at": 2_100_000_000,
            "open_id": "open-id",
            "scope": "video.publish",
            "client_audit_status": "approved",
        }
        values.update(overrides)
        path = Path(folder) / "tiktok-oauth.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path

    def test_probe_auth_uses_creator_readback_and_requires_public_visibility(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder)
            session = FakeSession([creator("PUBLIC_TO_EVERYONE", "SELF_ONLY")])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                result = upload_tiktok.probe_auth(session=session, now=1_900_000_000)

        self.assertEqual("valid", result["status"])
        self.assertTrue(result["ready"])
        self.assertTrue(result["readback"])
        self.assertEqual("thetradercockpit", result["creatorUsername"])
        self.assertEqual(upload_tiktok.CREATOR_INFO_URL, session.posts[0][0])
        self.assertEqual("Bearer access-token", session.posts[0][1]["headers"]["Authorization"])

    def test_probe_auth_reports_protected_operator_custody_without_crashing(self):
        with patch.object(Path, "is_file", side_effect=PermissionError("protected")):
            result = upload_tiktok.probe_auth(session=FakeSession([]), now=1_900_000_000)

        self.assertEqual("custody-unavailable", result["status"])
        self.assertFalse(result["ready"])

    def test_probe_auth_fails_closed_when_client_is_private_only(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder)
            session = FakeSession([creator("SELF_ONLY")])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                result = upload_tiktok.probe_auth(session=session, now=1_900_000_000)

        self.assertEqual("private-only", result["status"])
        self.assertFalse(result["ready"])
        self.assertTrue(result["readback"])

    def test_probe_auth_fails_closed_when_public_posting_audit_is_not_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder, client_audit_status="pending")
            session = FakeSession([creator("PUBLIC_TO_EVERYONE")])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                result = upload_tiktok.probe_auth(session=session, now=1_900_000_000)

        self.assertEqual("audit-required", result["status"])
        self.assertFalse(result["ready"])
        self.assertTrue(result["readback"])

    def test_expired_access_token_refreshes_and_persists_rotated_tokens(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(
                folder, access_token_expires_at=1_800_000_000
            )
            session = FakeSession([
                FakeResponse({
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 86_400,
                    "refresh_expires_in": 31_536_000,
                    "open_id": "open-id",
                    "scope": "video.publish",
                    "token_type": "Bearer",
                }),
                creator("PUBLIC_TO_EVERYONE"),
            ])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                result = upload_tiktok.probe_auth(session=session, now=1_900_000_000)

            saved = json.loads(credentials.read_text(encoding="utf-8"))

        self.assertTrue(result["ready"])
        self.assertEqual("new-access", saved["access_token"])
        self.assertEqual("new-refresh", saved["refresh_token"])
        refresh_url, refresh_request = session.posts[0]
        self.assertEqual(upload_tiktok.OAUTH_URL, refresh_url)
        self.assertEqual("refresh_token", refresh_request["data"]["grant_type"])
        creator_headers = session.posts[1][1]["headers"]
        self.assertEqual("Bearer new-access", creator_headers["Authorization"])

    def test_upload_returns_verified_post_id_url_and_receipt_readback(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder)
            video = Path(folder) / "clip.mp4"
            video.write_bytes(b"video-bytes")
            session = FakeSession([
                creator("PUBLIC_TO_EVERYONE", "SELF_ONLY"),
                ok({"publish_id": "publish-123", "upload_url": "https://upload.test/video"}),
                ok({
                    "status": "PUBLISH_COMPLETE",
                    "publicaly_available_post_id": ["post-456"],
                    "uploaded_bytes": len(b"video-bytes"),
                }),
            ], [FakeResponse(status_code=201)])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                result = upload_tiktok.upload(
                    video, "Caption #futures", session=session,
                    sleep=lambda _: None, now=1_900_000_000,
                )

        self.assertEqual("published", result["status"])
        self.assertEqual("post-456", result["id"])
        self.assertEqual(
            "https://www.tiktok.com/@thetradercockpit/video/post-456", result["url"]
        )
        self.assertEqual("post-456", result["platformResponse"]["readback"]["id"])
        init_payload = session.posts[1][1]["json"]
        self.assertEqual("PUBLIC_TO_EVERYONE", init_payload["post_info"]["privacy_level"])
        self.assertTrue(init_payload["post_info"]["is_aigc"])
        self.assertTrue(init_payload["post_info"]["brand_organic_toggle"])
        self.assertEqual("bytes 0-10/11", session.puts[0][1]["headers"]["Content-Range"])

    def test_upload_does_not_initialize_when_public_privacy_is_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder)
            video = Path(folder) / "clip.mp4"
            video.write_bytes(b"video")
            session = FakeSession([creator("SELF_ONLY")])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                with self.assertRaisesRegex(RuntimeError, "PUBLIC_TO_EVERYONE"):
                    upload_tiktok.upload(video, "Caption", session=session, now=1_900_000_000)

        self.assertEqual(1, len(session.posts))
        self.assertEqual([], session.puts)

    def test_upload_transmits_nothing_when_audit_is_not_recorded_as_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials = self.write_credentials(folder, client_audit_status="pending")
            video = Path(folder) / "clip.mp4"
            video.write_bytes(b"video")
            session = FakeSession([])
            with patch.object(upload_tiktok, "credential_path", return_value=credentials):
                with self.assertRaisesRegex(RuntimeError, "audit"):
                    upload_tiktok.upload(video, "Caption", session=session, now=1_900_000_000)

        self.assertEqual([], session.posts)
        self.assertEqual([], session.puts)


if __name__ == "__main__":
    unittest.main()
