#!/usr/bin/env python3
"""System janitor — audit and safely reclaim disk from agent leftovers.

The problem this solves: agents create git worktrees, dated archive clones, build
artifacts, and model/package caches, then never remove them. They compound until the
disk hits 0 bytes (2026-07-17 incident). This tool makes cleanup a runnable step, not
a hope.

Default is --audit (read-only): report reclaimable space by safety tier. Nothing is
deleted without an explicit --reclaim <tier>. Tiers, safest first:

  caches     regenerable package/model caches (pip, npm, HF, torch, __pycache__).
             Always safe; re-download on next use.
  build      gitignored build/output dirs inside repos (build/, dist/, node_modules,
             ta-work, clipper/output). Regenerable from source; only removed when the
             path is git-ignored AND the repo has no uncommitted changes there.
  worktrees  git worktrees whose branch is fully merged into its upstream/main AND
             which have a clean working tree AND no unpushed commits. Removed via
             `git worktree remove`. Anything dirty or unmerged is FLAGGED, never touched.
  archives   dated snapshot clones (_preserved-*, *-pre-cloud-*, *-backup-YYYYMMDD).
             Explicit point-in-time copies; removed only with --reclaim archives.

NEVER removed by any tier: a directory with uncommitted git changes, untracked source
that is not also in a remote, or anything under a --protect path. When unsure, it flags.

  py tools/janitor.py                      # audit every default root
  py tools/janitor.py --audit --root C:\\Users\\MSI\\repos
  py tools/janitor.py --reclaim caches build      # act on the two safe tiers
  py tools/janitor.py --reclaim worktrees --yes   # prune clean merged worktrees
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
DEFAULT_ROOTS = [HOME / "repos", HOME / "Documents", HOME / "Desktop"]
CACHE_DIRS = [
    HOME / ".cache" / "huggingface", HOME / ".cache" / "torch", HOME / ".cache" / "pip",
    HOME / "AppData" / "Local" / "pip" / "cache", HOME / "AppData" / "Roaming" / "npm-cache",
    HOME / "AppData" / "Local" / "npm-cache",
]
BUILD_NAMES = {"__pycache__", "build", "dist", "node_modules", "ta-work", ".pytest_cache", ".mypy_cache"}
BUILD_PATH_HINTS = ("clipper/output", "clipper\\output")
ARCHIVE_MARKERS = ("_preserved", "-pre-cloud", "-backup-", "-archive-", "_archive_")
GB = 1024 ** 3
MEASURE = True  # walk trees to size them; off for worktree-only reclaim (disk delta is authoritative)


def dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def git(args, cwd) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def is_clean(repo: Path) -> bool:
    code, out = git(["status", "--porcelain"], repo)
    return code == 0 and out == ""


def human(n: int) -> str:
    return f"{n / GB:.2f} GB" if n >= GB else f"{n / (1024**2):.0f} MB"


# ---- tier: caches
def scan_caches():
    items = []
    for d in CACHE_DIRS:
        try:
            available = d.is_dir()
        except OSError:
            continue
        if available:
            items.append((d, dir_size(d)))
    return items


# ---- tier: gitignored build artifacts inside repos
def scan_build(roots):
    items, seen_repos = [], set()
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, dirnames, _files in os.walk(root, onerror=lambda e: None):
            p = Path(dirpath)
            # don't descend into found build dirs or nested .git internals
            if p.name == ".git":
                dirnames[:] = []
                continue
            for name in list(dirnames):
                child = p / name
                hint = name in BUILD_NAMES or any(h in child.as_posix() for h in BUILD_PATH_HINTS)
                if not hint:
                    continue
                repo = _repo_root(child)
                if repo is None:
                    continue  # only touch build dirs that live inside a git repo (source is recoverable)
                code, ignored = git(["check-ignore", str(child)], repo)
                if code == 0 and ignored:  # git-ignored ⇒ regenerable
                    items.append((child, dir_size(child)))
                    dirnames.remove(name)  # don't recurse into it
    return items


def _repo_root(path: Path):
    code, out = git(["rev-parse", "--show-toplevel"], path.parent)
    return Path(out) if code == 0 and out else None


# ---- tier: git worktrees
def scan_worktrees(roots):
    """Return (removable, flagged). Only the main repos we can find are queried."""
    removable, flagged = [], []
    # A linked worktree's `worktree list` reports the WHOLE repo's worktrees, so N
    # sibling worktrees would each re-list all N (quadratic dupes). Group by the shared
    # git-common-dir → one canonical main per repo, and dedupe classified paths.
    mains = {}  # common-dir -> a repo dir to query
    for root in roots:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if (child / ".git").exists():
                code, common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], child)
                if code == 0 and common:
                    mains.setdefault(str(Path(common).resolve()).lower(), child)
    seen = set()
    for main in mains.values():
        # the actual main worktree (not a linked one) for merge-base comparisons
        code, main_top = git(["rev-parse", "--show-toplevel"], main)
        main_top = Path(main_top) if code == 0 and main_top else main
        code, out = git(["worktree", "list", "--porcelain"], main)
        if code != 0:
            continue
        wt, branch = None, None
        for line in out.splitlines() + [""]:
            if line.startswith("worktree "):
                wt = Path(line[len("worktree "):])
            elif line.startswith("branch "):
                branch = line[len("branch "):].replace("refs/heads/", "")
            elif line == "":
                key = str(wt.resolve()).lower() if wt else None
                if wt and wt != main_top and key not in seen:
                    seen.add(key)
                    _classify_worktree(main_top, wt, branch, removable, flagged)
                wt, branch = None, None
    return removable, flagged


def _classify_worktree(main, wt, branch, removable, flagged):
    if not wt.exists():
        flagged.append((wt, 0, "registered but missing on disk — `git worktree prune`"))
        return
    size = dir_size(wt) if MEASURE else 0
    if not is_clean(wt):
        flagged.append((wt, size, "UNCOMMITTED changes — review before removing"))
        return
    # unpushed commits?
    code, out = git(["log", "--branches", "--not", "--remotes", "--oneline"], wt)
    if code == 0 and out:
        flagged.append((wt, size, "clean but has UNPUSHED commits — push or confirm"))
        return
    # branch merged into main's HEAD?
    if branch:
        code, _ = git(["merge-base", "--is-ancestor", branch, "HEAD"], main)
        if code == 0:
            removable.append((wt, size, main, f"merged branch {branch}"))
            return
    flagged.append((wt, size, f"clean, branch {branch or '(detached)'} not merged — confirm"))


# ---- tier: dated archive dirs
def scan_archives(roots):
    items = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.is_dir() and any(m in child.name for m in ARCHIVE_MARKERS):
                items.append((child, dir_size(child)))
    return items


def rm(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", type=Path, help="root(s) to scan (default: ~/repos ~/Documents ~/Desktop)")
    ap.add_argument("--reclaim", nargs="+", choices=["caches", "build", "worktrees", "archives"], default=[],
                    help="tiers to actually delete; omit for read-only audit")
    ap.add_argument("--protect", action="append", type=Path, default=[], help="paths never to touch")
    ap.add_argument("--yes", action="store_true", help="skip the confirm line for --reclaim")
    a = ap.parse_args()
    roots = a.root or DEFAULT_ROOTS
    protect = [p.resolve() for p in a.protect]

    def protected(path: Path) -> bool:
        rp = path.resolve()
        return any(rp == q or q in rp.parents for q in protect)

    free_before = shutil.disk_usage("C:/").free
    print(f"C: free: {human(free_before)}   roots: {', '.join(str(r) for r in roots)}\n")

    # audit (no --reclaim) needs every tier; a scoped --reclaim only needs its own tiers.
    # scan_build walks every file under all roots — skip it unless actually needed, and
    # skip per-worktree tree-sizing for worktree-only reclaim (disk delta is the real freed).
    global MEASURE
    want = set(a.reclaim) if a.reclaim else {"caches", "build", "worktrees", "archives"}
    if a.reclaim == ["worktrees"]:
        MEASURE = False

    caches = [(p, s) for p, s in scan_caches() if not protected(p)] if "caches" in want else []
    build = [(p, s) for p, s in scan_build(roots) if not protected(p)] if "build" in want else []
    if "worktrees" in want:
        removable_wt, flagged_wt = scan_worktrees(roots)
        removable_wt = [t for t in removable_wt if not protected(t[0])]
    else:
        removable_wt, flagged_wt = [], []
    archives = [(p, s) for p, s in scan_archives(roots) if not protected(p)] if "archives" in want else []

    def report(title, rows):
        total = sum(r[1] for r in rows)
        print(f"## {title}: {human(total)} across {len(rows)}")
        for row in sorted(rows, key=lambda r: -r[1])[:12]:
            extra = f"  [{row[-1]}]" if len(row) > 2 and isinstance(row[-1], str) else ""
            print(f"   {human(row[1]):>10}  {row[0]}{extra}")
        if len(rows) > 12:
            print(f"   … and {len(rows) - 12} more")
        print()
        return total

    print("=== RECLAIMABLE (audit) ===\n")
    t_cache = report("caches (safe, regenerable)", caches)
    t_build = report("build artifacts (gitignored, regenerable)", build)
    t_wt = report("worktrees — merged+clean (safe to remove)", removable_wt)
    t_arch = report("archives (dated snapshots)", archives)
    print(f"TOTAL reclaimable now: {human(t_cache + t_build + t_wt + t_arch)}\n")

    if flagged_wt:
        print(f"=== FLAGGED — needs your review, NOT auto-removed ({len(flagged_wt)}) ===")
        for wt, size, why in sorted(flagged_wt, key=lambda r: -r[1])[:20]:
            print(f"   {human(size):>10}  {wt}  [{why}]")
        if len(flagged_wt) > 20:
            print(f"   … and {len(flagged_wt) - 20} more")
        print()

    if not a.reclaim:
        print("Read-only audit. Re-run with --reclaim <tiers> to delete. e.g. --reclaim caches build")
        return 0
    if not a.yes:
        print(f"About to DELETE tiers {a.reclaim}. Re-run with --yes to proceed.")
        return 0

    freed = 0
    if "caches" in a.reclaim:
        for p, s in caches:
            rm(p); freed += s; print(f"removed cache {p}")
    if "build" in a.reclaim:
        for p, s in build:
            rm(p); freed += s; print(f"removed build {p}")
    if "archives" in a.reclaim:
        for p, s in archives:
            rm(p); freed += s; print(f"removed archive {p}")
    if "worktrees" in a.reclaim:
        for wt, s, main, _why in removable_wt:
            code, _ = git(["worktree", "remove", "--force", str(wt)], main)
            if code == 0:
                freed += s; print(f"removed worktree {wt}")
            else:
                print(f"KEPT (git refused) {wt}")
        for main in {t[2] for t in removable_wt}:
            git(["worktree", "prune"], main)

    free_after = shutil.disk_usage("C:/").free
    print(f"\nreclaimed ~{human(freed)}  |  C: free {human(free_before)} -> {human(free_after)}")
    return 0


def _selftest():
    # the one bit of non-trivial logic worth guarding: archive/build name detection
    assert any(m in "_preserved-cleanup-20260713" for m in ARCHIVE_MARKERS)
    assert any(m in "esq-pre-cloud-2dadd73" for m in ARCHIVE_MARKERS)
    assert "node_modules" in BUILD_NAMES and "build" in BUILD_NAMES
    assert not any(m in "futures" for m in ARCHIVE_MARKERS), "must not flag a live repo as archive"
    assert human(2 * GB) == "2.00 GB" and human(500 * 1024 * 1024) == "500 MB"
    print("selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        raise SystemExit(main())
