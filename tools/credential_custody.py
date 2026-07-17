"""Operator-held publishing credential paths outside the repository."""

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPERATOR_CREDENTIAL_DIR = Path(r"C:\Users\MSI\.tradercockpit\operator-credentials")
ALLOWED_CREDENTIALS = {
    "client_secret.json",
    "token.json",
    "token_channel.json",
    "tiktok_session-tradercockpit.cookie",
    "meta.env",
    "telegram.env",
    "buttondown.env",
}


def operator_credential_dir() -> Path:
    path = Path(
        os.getenv("TRADERCOCKPIT_OPERATOR_CREDENTIAL_DIR", DEFAULT_OPERATOR_CREDENTIAL_DIR)
    ).expanduser().resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return path
    raise RuntimeError("operator credential directory must stay outside TraderCockpit")


def credential_path(name: str) -> Path:
    if name not in ALLOWED_CREDENTIALS:
        raise ValueError(f"unsupported credential file: {name}")
    return operator_credential_dir() / name


def load_meta_env() -> bool:
    """Load operator-held Meta publish credentials into the environment, if present.

    Fails closed: absent file (e.g. sandboxed agent without profile access)
    simply means Meta readiness probes report absent.
    """
    path = credential_path("meta.env")
    if not path.is_file():
        return False
    from dotenv import load_dotenv

    load_dotenv(path)
    return True
