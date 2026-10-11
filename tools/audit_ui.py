"""Strict UI audit — fails on NEW drift, grandfathers the old.

Checks (frontend/ only):
  color-literal  — #[hex] / rgb( / hsl( outside frontend/css/tokens.css
  console        — console.log|debug|warn|error in frontend/js
  dup-id         — same id="..." twice within ONE file (cross-file reuse is
                   fine: only one view is live at a time)
  ad-label       — <ins class="adsbygoogle" without an 'Advertisement'
                   caption in the 12 lines above it
  ad-client      — data-ad-client outside the allowlist (catches placeholders)

Grandfathered findings live in tools/audit_baseline.txt as
  <check>\\t<relpath>\\t<snippet>
A finding fails only if its (check, relpath, snippet) is NOT in the baseline.
To legitimize an old finding, delete its baseline line AND fix the code —
never just re-baseline.

Usage:  python tools/audit_ui.py [--regen-baseline]
Exit 1 on new findings.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "frontend"
TOKENS_CSS = FRONT / "css" / "tokens.css"
BASELINE = Path(__file__).resolve().parent / "audit_baseline.txt"

AD_CLIENT_ALLOW = {"ca-pub-4540036176937342"}

# Identity of a finding: (check, file, snippet prefix). The full snippet is
# diagnostic only — prefixes survive formatting shifts and line-ending
# conversions that would otherwise false-positive on every run.
KEY_LEN = 80


def key_of(check, relpath, snippet):
    # rstrip: an 80-char cut may end mid-whitespace; trailing spaces are
    # meaningless for identity and fragile across editors/line-endings.
    return "\t".join([check, relpath, snippet[:KEY_LEN].rstrip()])

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\s*\(|hsla?\s*\(")
CONSOLE_RE = re.compile(r"console\.(log|debug|warn|error)\s*\(")
ID_RE = re.compile(r'id="([^"]+)"')
INS_RE = re.compile(r'<ins\s+class="adsbygoogle"')
CLIENT_RE = re.compile(r'data-ad-client="([^"]+)"')


def load_baseline():
    known = set()
    if BASELINE.is_file():
        for line in BASELINE.read_text().splitlines():
            if line and not line.startswith("#"):
                known.add(line)
    return known


def snippet_of(text):
    return re.sub(r"\s+", " ", text.strip())[:120]


VENDOR_CSS = {"pico.min.css"}  # third-party, never audited


def iter_front_files():
    for p in sorted((FRONT / "js").glob("*.js")):
        yield p
    for p in [FRONT / "index.html", FRONT / "sw.js"]:
        if p.is_file():
            yield p
    for p in sorted((FRONT / "css").glob("*.css")):
        if p.name in VENDOR_CSS:
            continue
        yield p


def audit():
    findings = []  # (check, relpath, line, snippet)
    for path in iter_front_files():
        rel = path.relative_to(ROOT).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        seen_ids = {}
        for i, line in enumerate(lines, 1):
            if path != TOKENS_CSS and COLOR_RE.search(line):
                # href="#/..." anchors: '#' followed by non-hex can't match, safe
                findings.append(("color-literal", rel, i, snippet_of(COLOR_RE.search(line).group(0) + " :: " + line)))
            if path.suffix == ".js" and CONSOLE_RE.search(line):
                findings.append(("console", rel, i, snippet_of(line)))
            for m in ID_RE.finditer(line):
                ident = m.group(1)
                if ident in seen_ids:
                    findings.append(("dup-id", rel, i, f'id="{ident}" also line {seen_ids[ident]}'))
                else:
                    seen_ids[ident] = i
            for m in INS_RE.finditer(line):
                window = "\n".join(lines[max(0, i - 13):i - 1])
                if "Advertisement" not in window:
                    findings.append(("ad-label", rel, i, snippet_of(line)))
            for m in CLIENT_RE.finditer(line):
                if m.group(1) not in AD_CLIENT_ALLOW:
                    findings.append(("ad-client", rel, i, snippet_of(line)))
    return findings


def main():
    findings = audit()
    known = load_baseline()
    new = [f for f in findings if key_of(f[0], f[1], f[3]) not in known]
    if "--regen-baseline" in sys.argv:
        BASELINE.write_text(
            "# Grandfathered UI findings (check\\trelpath\\tsnippet). "
            "Fix code + delete line to un-grandfather; never re-baseline blindly.\n"
            + "\n".join(key_of(c, p, s) for c, p, _ln, s in sorted(findings)) + "\n"
        )
        print(f"baseline regenerated: {len(findings)} findings")
        return 0
    if new:
        print(f"FAIL: {len(new)} NEW UI finding(s) (baseline has {len(known)} grandfathered):")
        for check, rel, line, snip in new:
            print(f"  [{check}] {rel}:{line}: {snip}")
        print("Fix the code (tokens/components specs), then extend the baseline only for deliberate exceptions.")
        return 1
    print(f"OK: {len(findings)} findings, all grandfathered in baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
