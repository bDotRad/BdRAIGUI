# SSH Key Convention

Standard for every SSH deploy key generated on BdRAIGUI (this host) for
reaching another machine or a git remote. Applies fleet-wide — any project
under `~/projects/` that needs a new key should follow this rather than
inventing its own naming.

## Naming

- **Filename**: `<source>_to_<target>`, snake_case, no file extension for
  the private half (`.pub` suffix for the public half). `source` is
  almost always `bdraigui` (this host) unless the key is generated
  elsewhere and copied in.
- **Comment** (the trailing field in the `.pub` line): `<Source>-to-<Target>`,
  same pairing as the filename but PascalCase, no separating punctuation
  inside `<Target>`. Append the target's *kind* directly onto its name,
  no hyphen: `...Server` for a VM/box you SSH into, `...GIT` for a git
  remote/deploy key. Examples:
  - `bdraigui_to_planbdradserver` / comment `BdRAIGUI-to-PlanBdRadServer`
  - `bdraigui_to_planbdradgit` / comment `BdRAIGUI-to-PlanBdRadGIT`
  - `bdraigui_to_bdraiguigit` / comment `BdRAIGUI-to-BdRAIGUIGIT`

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
  Raspberry Pi.** This host (BdRAIGUI, hostname `BdRDev`) is not a Pi —
  don't call it one in new keys. (`id_ed25519_pi` is a legitimate
  exception: it really does reach a physical Pi, `BdRadBirdDetector` at
  `192.168.1.187`, for the BdRBirdDetector project.)

## Current inventory (as of 2026-08-24)

| File | Target | Purpose |
|---|---|---|
| `bdraigui_to_bdraiguigit` | `github.com:bDotRad/BdRAIGUI.git` | This project's own deploy key (via `~/.ssh/config` alias `github.com-bdraigui`) |
| `bdraigui_to_planbdradgit` | `github.com:bDotRad/PlanBdRad.git` | PlanBdRad repo deploy key, confirmed read+write |
| `bdraigui_to_planbdradserver` | `bdr@192.168.100.20` (`PlanBdRadServer`) | Deploy access to the PlanBdRad VM — not yet installed in the VM's `authorized_keys` as of this writing |
| `id_ed25519_pi` | `bdotrad@192.168.1.187` (`BdRadBirdDetector`) | Legitimate physical-Pi exception, see above |
| `id_ed25519` | unknown | Not referenced by any project doc or `~/.ssh/config` entry — unexplained, flagged for cleanup but not yet resolved |

**Known open item, not yet addressed**: `~/.ssh/authorized_keys` on
BdRAIGUI itself (i.e. what's allowed to SSH *into* this host) currently
trusts a key with comment `PlanBdRad` that doesn't match any private key
found on this host — likely a leftover from the same mixup that affected
`bdraigui_to_planbdradserver`. Worth reviewing/removing once its origin
is confirmed.
