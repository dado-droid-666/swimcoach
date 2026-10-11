# Token layer (closed set)

Canonical file: `frontend/css/tokens.css` (loaded after `pico.min.css` and
`style.css`; identical values to the legacy mirror => zero visual diff).

## Rule
- UI code (CSS, JS templates, `index.html`) uses **only** `var(--name)`.
- Need a new color/spacing/radius? **Add the token first**, then use it.
- `tools/audit_ui.py` fails CI on any `#[hex]` / `rgb(` / `hsl(` literal
  outside `tokens.css`.

## Known drift (grandfathered, do not copy)
These predate the token layer and are consolidated in Session B:
- `style.css` legacy `:root` mirror (identical values — frozen, no new vars).
- `--warning-color: #F59E0B` uppercase in legacy mirror (canonical is `#f59e0b`).
- Wave `fill=` attributes in `index.html` (now tokenized as `--wave-1/2/3`).
- Phase colors were inline in `app.js:getPhaseColor` (now `--phase-*`).
- Install banner text `--primary` on `#06333b` (now `--text-on-primary`).

## Token table
| Token | Value | Use |
|---|---|---|
| `--primary` | `#3fd0e6` | Accent: links, primary buttons, active states |
| `--primary-hover` | `#2bb8cf` | Hover on primary |
| `--primary-background` | `#3fd0e622` | Tinted fills (pills selected, highlights) |
| `--success-color` / `--success-background` | `#2ecc71` / `…22` | Success states, Pro badges |
| `--warning-color` / `--warning-background` | `#f59e0b` / `…22` | Warnings, Build phase |
| `--error-color` / `--error-background` | `#ff3b5c` / `…22` | Errors, destructive zones |
| `--muted-color` | `#9db6cc` | Secondary text, captions |
| `--muted-background` | `#0e2b45cc` | Muted fills |
| `--border-color` | `#1f4b6b` | Borders, dividers |
| `--bg-deep` | `#061a2e` | Page background |
| `--bg-card` / `--bg-card2` | `#0e2b45cc` / `#154466cc` | Cards, modals, inputs |
| `--text-ocean` | `#f2f7fb` | Primary text |
| `--text-on-primary` | `#06333b` | Text on aqua fills |
| `--phase-base/build/peak/taper/race/unknown` | greens…grays | Macrocycle badges + week bars |
| `--wave-1/2/3` | `#1c86ba/#146f9e/#0e5c86` | Landing background waves |
| `--spacing-xs…xl` | `0.25…2rem` | Margins/padding |
| `--radius-sm/md/lg/full` | `0.25/0.5/1/9999px` | Corners |
| `--shadow-sm/md/lg` | … | Elevation |
