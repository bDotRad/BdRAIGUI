## What was done

Brad asked to see the basic standard project tree established in
`_Instructions/ProjectSetup.md` (from the prior `rStandardiseProjectMD`
request), and whether a `.claude` / `.human` folder split would be
easier than the current layout.

**The standard tree** (per `ProjectSetup.md`, as scaffolded on
`BdRAMAssist`):

```
<project>/
├── CLAUDE.md              # agent-facing: how the scheduler wakes/kills
│                          # this session, gotchas, conventions
├── Description.md         # human-facing: short summary of what the
│                          # project is/does
├── .claude/
│   └── agents/
│       └── <slug>/
│           └── <slug>.md  # one subagent definition per folder
└── References/
    └── README.md          # placeholder; site-specific docs Brad drops
                            # in by hand (not parsed by any tooling)
```

**On the `.claude` / `.human` idea:** recommended against moving
`CLAUDE.md` and `Description.md` off the root into a `.claude`/`.human`
split, for a concrete reason rather than just style preference:

- Claude Code itself auto-loads `CLAUDE.md` as project memory only from
  the repo root (and parent dirs) — not from an arbitrary path inside
  `.claude/`. Moving it would silently stop it from being read at
  session start.
- The dashboard hardcodes the same assumption: `list_agent_files()` in
  `app/common.py` looks for `proj_dir / "CLAUDE.md"` specifically, and
  `find_description_file()` looks for `Description.md`/`description.md`
  at root. Relocating either file breaks the dashboard's "Claude agent
  files" and "Description" panels without a matching code change.
- The underlying instinct — separate what's Claude-authored/-read from
  what's human-authored/-read — is already there in lighter form:
  `.claude/agents/` is Claude Code's own native subagent format, and
  `References/` already plays the "human drops stuff in" role. A
  `.human` wrapper folder would only ever hold `Description.md` +
  `References/`, which isn't enough content to justify the extra
  nesting, and `.claude/` already has fixed meaning to Claude Code
  tooling (settings, commands, hooks, agents) — folding a project's own
  arbitrary docs into it risks confusion with that.

So: keep the current root-level `CLAUDE.md` + `Description.md`, with
`.claude/agents/` and `References/` as the two purpose-built
subfolders. No convention doc changes needed — this confirmed the
existing `ProjectSetup.md` stands as written.

**Outcome:** answered, no code or doc changes.

---

READY

Can you show me the basic standard tree for a new project that I recently requested. Include the standard files.

Is it easier to have a .claude and a .human folder.

.claude is for claude, .human is hor humans.
