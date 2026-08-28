WAITING RESPONSE

## Built — review the structure (Claude, 2026-08-28)

Set up the two-layer system you described:

**Layer 1 — generic / fleet-wide.** Put it in the existing
**`BdRDev/_Instructions/`** folder (rather than a new `_Standards/`) —
that folder already holds the fleet-wide generic docs (`ProjectSetup`,
`SSH`, `Requests`, `AppServerSync`), so this extends it rather than
splitting conventions across two places. New files:
- `_Instructions/Standards.md` — describes the two-layer model itself,
  indexes every Layer-1 doc, and states the precedence rules
  (project overrides win where explicit; silence = inherit; don't fork
  a Layer-1 doc into a project).
- `_Instructions/WebUI.md` — the first real generic web standard: look &
  feel, versioning (= deployed 7-char commit SHA, shown under the
  title), and the Edit/Save/Cancel table pattern (`rEditing Tables`).
  "Setting up servers" is covered by pointing at the existing
  `BdRPiAMI-PROVISION.md` worked example.

**Layer 2 — project-specific.** No new file per project. Precedence and
the "only document deviations" rule are written into `Standards.md`;
pointers added to `CLAUDE.md`, `_Instructions/ProjectSetup.md`, and
`_Instructions/BdRDev.md` (the doc that gets copied into other
projects' context) so every project's session learns the top layer
exists.

**Your call:** happy with it living in `_Instructions/`? Want a
dedicated `_Standards/` folder or a separate repo instead? Any other
Layer-1 topics to stub now (forms, auth, deploy)? Committed + pushed —
flip to READY with notes or archive.

---

In reference to the Editing Tables request, i think i need a 2 layer .md system.

Top layer is for generic stuff like setting up servers, basics for web pages like versioning etc. Editing tables like i mentioned.

THen down a layer at the project level, is project specific instructions. so that all projects receive the same overall look and feel unless otherwise specified.
