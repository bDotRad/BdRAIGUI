# SSH Key Convention

Standard for every SSH deploy key generated on BdRDev (this host) for
reaching another machine or a git remote. Applies fleet-wide — any project
under `~/projects/` that needs a new key should follow this rather than
inventing its own naming.

## Naming

- **Filename**: `<source>_to_<target>`, snake_case, no file extension for
  the private half (`.pub` suffix for the public half). `source` is
  almost always `bdrdev` (this host) unless the key is generated
  elsewhere and copied in. **2026-08-25 note**: this host's actual
  *machine* hostname is being changed to `BdRSrvDev` (see MIGRATION_REPORT.md
  in `~/projects/`) — `BdRDev` remains the *project/app* name. Existing
  keys below keep the `bdrdev_` prefix from today's BdRAIGUI→BdRDev
  rename; going forward, judgment call needed on whether new keys should
  key off the app name (`bdrdev_`) or the machine hostname (`bdrsrvdev_`)
  — not resolved as part of this pass.
- **Comment** (the trailing field in the `.pub` line): `<Source>-to-<Target>`,
  same pairing as the filename but PascalCase, no separating punctuation
  inside `<Target>`. Append the target's *kind* directly onto its name,
  no hyphen: `...Server` for a VM/box you SSH into, `...GIT` for a git
  remote/deploy key. Examples:
  - `bdrdev_to_planbdradserver` / comment `BdRDev-to-PlanBdRadServer`
  - `bdrdev_to_planbdradgit` / comment `BdRDev-to-PlanBdRadGIT`
  - `bdrdev_to_bdrdevgit` / comment `BdRDev-to-BdRDevGIT`

## Rules

- **One key per (source, target) pair.** Never reuse a key across
  unrelated targets, and never leave a generic/unlabeled key
  (`id_ed25519` with no comment or doc reference) sitting around — if you
  can't say in one line what it's for, it shouldn't exist.
- **Document it in the owning project's setup doc** (e.g. `VM_SETUP.md`,
  `CLAUDE.md`) — purpose, where the public half was installed (target's
  `authorized_keys`, or a git host's deploy-key UI), and the date
  generated.
- **Never trust an existing `.pub` file blindly.** Before writing a key
  into any doc or handing it to Brad to paste somewhere, derive it fresh
  from the private key and diff:
  ```
  ssh-keygen -y -f ~/.ssh/<name>
  ```
  A `.pub` file can silently drift from its private key (wrong content
  pasted over it, stale copy, etc.) — this already happened once
  (2026-08-24, the PlanBdRad VM key) and cost several rounds of back-and-forth
  before anyone thought to check. Confirm the current file matches the
  ssh-keygen -y output before treating it as ground truth.
- **No "Pi" in names/comments unless the target genuinely is a physical
  Raspberry Pi.** This host (project `BdRDev`; machine hostname is still
  `BdRDev` as of 2026-08-26 — a rename to `BdRSrvDev` was planned
  2026-08-25 but the `sudo hostnamectl set-hostname` step hasn't actually
  been run yet, see MIGRATION_REPORT.md) is not a Pi — don't call it one
  in new keys. (`id_ed25519_pi` is a legitimate exception: it really does
  reach a physical Pi, `BdRadBirdDetector` at `192.168.1.187`, for the
  BdRBirdDetector project.)

## Current inventory (as of 2026-08-26)

| File | Target | Purpose |
|---|---|---|
| `bdrdev_to_bdrdevgit` | `github.com:bDotRad/BdRDev.git` | This project's own deploy key (via `~/.ssh/config` alias `github.com-bdrdev`) |
| `bdrdev_to_planbdradgit` | `github.com:bDotRad/PlanBdRad.git` | PlanBdRad repo deploy key, confirmed read+write |
| `bdrdev_to_planbdradserver` | `bdr@192.168.100.20` (`PlanBdRadServer`) | Deploy access to the PlanBdRad VM — not yet installed in the VM's `authorized_keys` as of this writing |
| `bdrdev_to_bdramassistgit` | `github.com:bDotRad/BdRAMAssist.git` | BdRAMAssist repo deploy key, generated 2026-08-26 — **not yet installed** as a deploy key on GitHub (adding it via API was blocked by a safety check); current push access is via the account-level `gh` HTTPS credential helper instead. Add the `.pub` under the repo's Settings -> Deploy keys (with write access) to switch to this SSH key. |
| `bdrdev_to_bdrdungeongit` | `github.com:bDotRad/BdRDungeon.git` | BdRDungeon repo deploy key, generated 2026-08-26 — same not-yet-installed situation as the BdRAMAssist key above; pushing via `gh` HTTPS credential helper for now. |
| `id_ed25519_pi` | `bdotrad@192.168.1.187` (`BdRadBirdDetector`) | Legitimate physical-Pi exception, see above |
| `id_ed25519` | unknown | Not referenced by any project doc or `~/.ssh/config` entry — unexplained, flagged for cleanup but not yet resolved |

**Known open item, not yet addressed**: `~/.ssh/authorized_keys` on
BdRDev itself (i.e. what's allowed to SSH *into* this host) currently
trusts a key with comment `PlanBdRad` that doesn't match any private key
found on this host — likely a leftover from the same mixup that affected
`bdrdev_to_planbdradserver`. Worth reviewing/removing once its origin
is confirmed.

**2026-08-25**: all four `bdraigui_*` key files renamed to `bdrdev_*`
(content unchanged, filenames/`~/.ssh/config` only) as part of the
BdRAIGUI→BdRDev project rename. See MIGRATION_REPORT.md.
