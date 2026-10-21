"""Spec sync check — code changes must ride with their spec (sync rule).

Buckets (Session A AI-ready):
  UI code       frontend/js/*.js, frontend/css/*.css (except tokens.css),
                frontend/index.html, frontend/sw.js
                => docs/specs/components.md | patterns.md | tokens.md | principles.md
  training code backend/services/{swim_generator,strength_generator,
                adaptive_state,macrocycle_calculator,salo_mix,css_zones,
                load_model}.py, backend/routes/{competition,plan}.py,
                data/*.json
                => docs/specs/training.md (+ principles.md for product calls)

Compares the push diff (event.before..sha in CI; HEAD~1..HEAD locally or
--base/--head overrides). Docs-only commits pass trivially. No git context
(e.g. fresh archive) => pass with a note.

Usage: python tools/audit_spec.py [--base X --head Y]
Exit 1 when a bucket is touched without its spec file in the same diff.
"""
import subprocess
import sys

UI_CODE = ("frontend/js/", "frontend/css/", "frontend/index.html", "frontend/sw.js")
UI_SPEC = ("docs/specs/components.md", "docs/specs/patterns.md",
           "docs/specs/tokens.md", "docs/specs/principles.md", "docs/llms.txt")
TRAIN_CODE = ("backend/services/swim_generator", "backend/services/strength_generator",
              "backend/services/adaptive_state", "backend/services/macrocycle_calculator",
              "backend/services/salo_mix", "backend/services/css_zones",
              "backend/services/load_model", "backend/routes/competition",
              "backend/routes/plan", "data/")
TRAIN_SPEC = ("docs/specs/training.md", "docs/specs/principles.md", "docs/llms.txt")

# tokens.css (mechanical) and the audit baseline never demand a spec.
# NOTE: do not filter docs/ here — spec files must stay in the diff so
# UI_SPEC/TRAIN_SPEC can match them. Docs are not in the code buckets.
ALWAYS_OK = ("frontend/css/tokens.css", "tools/audit_baseline.txt")


def changed_files(base, head):
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        return [l.strip() for l in out if l.strip()]
    except Exception:
        return None


def bucket_hit(files, prefixes):
    return [f for f in files if f.startswith(prefixes)]


def main():
    args = sys.argv[1:]
    base = head = None
    if "--base" in args:
        base = args[args.index("--base") + 1]
    if "--head" in args:
        head = args[args.index("--head") + 1]
    if base is None or head is None:
        import os
        base = os.environ.get("AUDIT_BASE", "HEAD~1")
        head = os.environ.get("AUDIT_HEAD", "HEAD")
    files = changed_files(base, head)
    if files is None:
        print("audit_spec: no git context, skipping (pass).")
        return 0
    files = [f for f in files if not f.startswith(ALWAYS_OK)]
    problems = []
    ui = bucket_hit(files, UI_CODE)
    if ui and not bucket_hit(files, UI_SPEC):
        problems.append(f"UI code touched without spec update: {', '.join(ui[:5])}"
                        + ("…" if len(ui) > 5 else ""))
    tr = bucket_hit(files, TRAIN_CODE)
    if tr and not bucket_hit(files, TRAIN_SPEC):
        problems.append(f"training code touched without spec update: {', '.join(tr[:5])}"
                        + ("…" if len(tr) > 5 else ""))
    if problems:
        print("FAIL: spec sync rule violated:")
        for p in problems:
            print("  " + p)
        return 1
    print(f"OK: spec sync holds ({len(files)} file(s) in diff).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
