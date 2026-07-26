"""Machine-dependent directories that live outside the repository.

Defaults are the operator's Windows box; every path is overridable by env var so
the same checkout runs on the Linux box. Same contract as `credential_custody`.
"""

import os
from pathlib import Path


DEFAULTS = {
    "TRADERCOCKPIT_VAULT_DIR": r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit",
    "TRADERCOCKPIT_LEGACY_VAULT_DIR": r"C:\Users\MSI\Desktop\TraderCockpit-Vault",
    "TRADERCOCKPIT_MANAGER_DIR": r"C:\Users\MSI\Documents\Manager\vault",
    "TRADERCOCKPIT_TV_CLI": r"C:\Users\MSI\repos\tradingview-mcp\src\cli\index.js",
}


def _resolve(var: str) -> Path:
    # not .resolve() — a Windows default resolved on Linux becomes cwd-relative nonsense
    return Path(os.getenv(var) or DEFAULTS[var]).expanduser()


def vault_dir() -> Path:
    """The live ops vault (Board, Coordination, GTM, Needs-You)."""
    return _resolve("TRADERCOCKPIT_VAULT_DIR")


def legacy_vault_dir() -> Path:
    """The tombstoned TraderCockpit-Vault. Read-only; only `morning_rundown` still reads it."""
    return _resolve("TRADERCOCKPIT_LEGACY_VAULT_DIR")


def manager_dir() -> Path:
    """Manager's local receipt store. Local-only ledger — absent on any box but the operator's."""
    return _resolve("TRADERCOCKPIT_MANAGER_DIR")


def tv_cli() -> Path:
    """tradingview-mcp's `tv` CLI entry. Node + CDP, so not itself Windows-bound —
    only its checkout is, until that repo lands somewhere both boxes can reach."""
    return _resolve("TRADERCOCKPIT_TV_CLI")


def missing() -> list[str]:
    """Env vars whose target does not exist here — for a box's readiness probe.
    Uses exists(), not is_dir(): TRADERCOCKPIT_TV_CLI points at a file."""
    return [var for var in DEFAULTS if not _resolve(var).exists()]
