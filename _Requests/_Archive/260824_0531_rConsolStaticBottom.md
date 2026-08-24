## What was done

The screenshot showed the Console modal's pane snapshot ending in a block of
static UI chrome — a box-drawing rule, the empty input box, the
`auto mode on ... /rc` mode line, and (when background agents are running)
the agent status list. That's Claude Code's own fixed bottom-of-terminal UI,
redrawn in place every frame; it's not part of the conversation and doesn't
change between refreshes, so it was just clutter at the bottom of every
snapshot.

`tmux_capture()` in `app/common.py` does a raw `tmux capture-pane`, which
captures that chrome along with the real transcript. Added
`_strip_cli_chrome()`: it looks for the topmost Unicode box-drawing rule
(`─` repeated) within the last 20 lines of the capture and truncates
everything from there down, since that rule is a reliable, stable marker for
"static UI starts here" — it always appears immediately above the input box.
Wired into `tmux_capture()` so both `/api/console/<project>` and its
`/send` counterpart see the trimmed content.

Verified against the live `_BdRAIGUI` tmux session (`proj-_BdRAIGUI`) before
and after: raw capture ended in the rule + input box + mode line; after the
fix, `tmux_capture()` returns just the transcript up to (not including) the
rule.

Restarted the live dashboard (`kill -9` on the systemd-managed process, which
triggers `Restart=on-failure`) to pick up the change, and confirmed via
`curl http://127.0.0.1:8420/api/console/_BdRAIGUI` that the trimmed content is
now served.

Fixed and deployed — no further action needed.

---

READY

Why is there static stuff at the bottom.

can we hide
