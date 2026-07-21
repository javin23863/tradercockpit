#!/usr/bin/env python3
"""Build the HUD skill catalog from installed packages and Claude usage metadata."""

import hashlib
import json
import mmap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USER = ROOT.parents[1]
OUT = ROOT / "social-ops" / "skill-catalog.json"
USAGE_CACHE = ROOT / "social-ops" / ".skill-usage-cache.json"
DEFAULT_ROOTS = (
    ("codex", USER / ".codex" / "skills"),
    ("shared", USER / ".agents" / "skills"),
    ("claude", USER / ".claude" / "skills"),
    ("claude-plugin", USER / ".claude" / "plugins" / "cache"),
    ("project", ROOT / ".agents" / "skills"),
    ("codex-plugin", USER / ".codex" / "plugins" / "cache"),
)
DEFAULT_USAGE = USER / ".claude" / "projects"
GATED = {
    "esq-battery-ops": "operator-gated compute",
    "social-ops-luna": "publication workflow",
    "tiktok-upload": "public upload and credentials",
    "vastai-fanout": "external spend and compute",
    "github:yeet": "GitHub mutation and deployment",
    "yeet": "GitHub mutation and deployment",
}
DESCRIPTION_PRIORITY = {
    "project": 5,
    "shared": 4,
    "codex": 3,
    "claude": 2,
    "codex-plugin": 1,
    "claude-plugin": 1,
}


def _frontmatter(path):
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None
    if not lines:
        return None
    if lines[0].strip() != "---":
        description = next((line.strip() for line in lines[1:] if line.strip() and not line.lstrip().startswith("#")), "Legacy Claude workflow.")
        return {"name": path.parent.name, "description": description[:320]}
    data = {}
    index = 1
    while index < len(lines) and lines[index].strip() != "---":
        line = lines[index]
        key, separator, value = line.partition(":")
        key = key.strip()
        if separator and key in {"name", "description"}:
            value = value.strip().strip("\"'")
            if value in {">", "|"}:
                parts = []
                index += 1
                while index < len(lines) and (not lines[index].strip() or lines[index][0].isspace()):
                    if lines[index].strip():
                        parts.append(lines[index].strip())
                    index += 1
                data[key] = " ".join(parts)
                continue
            data[key] = value
        index += 1
    if not data.get("name"):
        data["name"] = path.parent.name
    data.setdefault("description", "No description recorded.")
    return data


def _scan_usage_file(filename):
    counts, latest = Counter(), {}
    needles = (b'"name":"Skill"', b'"name": "Skill"')
    try:
        handle = filename.open("rb")
    except OSError:
        return counts, latest
    with handle:
        try:
            history = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        except (OSError, ValueError):
            return counts, latest
        with history:
            starts = set()
            for needle in needles:
                cursor = 0
                while (hit := history.find(needle, cursor)) >= 0:
                    starts.add(history.rfind(b"\n", 0, hit) + 1)
                    cursor = hit + len(needle)
            lines = []
            for start in starts:
                end = history.find(b"\n", start)
                lines.append(history[start : len(history) if end < 0 else end])
    for line in lines:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            continue
        message = event.get("message") if isinstance(event, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("name") != "Skill":
                continue
            inputs = item.get("input") if isinstance(item.get("input"), dict) else {}
            name = str(inputs.get("skill") or "").strip()
            if not name:
                continue
            counts[name] += 1
            stamp = str(event.get("timestamp") or "")
            if stamp > latest.get(name, ""):
                latest[name] = stamp
    return counts, latest


def _claude_usage(root, cache_path=None):
    counts, latest = Counter(), {}
    if not root or not Path(root).is_dir():
        return counts, latest
    cached = {}
    if cache_path and Path(cache_path).is_file():
        try:
            cached = json.loads(Path(cache_path).read_text(encoding="utf-8")).get("files", {})
        except (OSError, json.JSONDecodeError, AttributeError):
            cached = {}
    current = {}
    for filename in Path(root).rglob("*.jsonl"):
        try:
            stat = filename.stat()
        except OSError:
            continue
        key = str(filename.resolve())
        fingerprint = f"{stat.st_size}:{stat.st_mtime_ns}"
        item = cached.get(key, {})
        if item.get("fingerprint") == fingerprint:
            file_counts = Counter(item.get("counts", {}))
            file_latest = item.get("latest", {})
        else:
            file_counts, file_latest = _scan_usage_file(filename)
        current[key] = {"fingerprint": fingerprint, "counts": dict(file_counts), "latest": file_latest}
        counts.update(file_counts)
        for name, stamp in file_latest.items():
            if stamp > latest.get(name, ""):
                latest[name] = stamp
    if cache_path:
        cache_path = Path(cache_path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"schema": "claude-skill-usage-cache/v1", "files": current}), encoding="utf-8")
    return counts, latest


def build_catalog(roots=DEFAULT_ROOTS, usage_root=DEFAULT_USAGE, usage_cache=None):
    packages = {}
    for kind, base in roots:
        base = Path(base)
        if not base.is_dir():
            continue
        for path in base.rglob("SKILL.md"):
            metadata = _frontmatter(path)
            if not metadata:
                continue
            name = metadata["name"]
            item = packages.setdefault(name, {
                "name": name,
                "description": metadata["description"],
                "description_priority": -1,
                "sources": [],
            })
            priority = DESCRIPTION_PRIORITY.get(kind, 0)
            if priority > item["description_priority"]:
                item["description"] = metadata["description"]
                item["description_priority"] = priority
            source = {"kind": kind, "path": str(path)}
            if source not in item["sources"]:
                item["sources"].append(source)

    counts, latest = _claude_usage(usage_root, usage_cache)
    aliases = {}
    for invoked in list(counts):
        canonical = invoked.split(":", 1)[-1] if ":" in invoked else invoked
        if canonical == invoked or canonical not in packages:
            continue
        counts[canonical] += counts.pop(invoked)
        latest[canonical] = max(latest.get(canonical, ""), latest.pop(invoked, ""))
        aliases.setdefault(canonical, []).append(invoked)
    for name in counts:
        packages.setdefault(name, {"name": name, "description": "Invoked by Claude Code but no local SKILL.md was found.", "sources": []})

    skills = []
    for name, item in packages.items():
        item.pop("description_priority", None)
        item["sources"].sort(key=lambda source: (source["kind"], source["path"]))
        item["source_kinds"] = sorted({source["kind"] for source in item["sources"]})
        item["available"] = bool(item["sources"])
        item["claude_used_count"] = counts[name]
        item["last_claude_use"] = latest.get(name)
        item["claude_aliases"] = sorted(aliases.get(name, []))
        if not item["available"]:
            item["hud_mode"] = "missing"
            item["gate_reason"] = "workflow source is not installed locally"
        elif name in GATED:
            item["hud_mode"] = "gated"
            item["gate_reason"] = GATED[name]
        else:
            item["hud_mode"] = "prompt"
            item["gate_reason"] = None
        skills.append(item)
    skills.sort(key=lambda item: (-item["claude_used_count"], item["name"].casefold()))
    payload = {
        "schema": "apollo-skill-catalog/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "skills": len(skills),
            "installed": sum(item["available"] for item in skills),
            "claude_used": sum(item["claude_used_count"] > 0 for item in skills),
            "missing": sum(not item["available"] for item in skills),
            "gated": sum(item["hud_mode"] == "gated" for item in skills),
        },
        "skills": skills,
    }
    digest_source = json.dumps(payload["skills"], sort_keys=True, separators=(",", ":")).encode()
    payload["catalog_hash"] = hashlib.sha256(digest_source).hexdigest()
    return payload


def main():
    payload = build_catalog(usage_cache=USAGE_CACHE)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(OUT)
    print(json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
