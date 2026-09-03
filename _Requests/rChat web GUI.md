WAITING RESPONSE

## Original ask (Brad, 2026-09-04, moved here from `rEcosystem fold-apps Part C.md`)

> Im going to chat through the CLI. i find this window painful to use. i
> want to set up char web gui to make it easier

## What an unattended pass found (2026-09-04)

**A working chat web GUI already exists on this box and is running right
now.** It looks like you (or a session on `bdrpisrvami`/elsewhere) set it
up on 2026-09-03 and it just isn't wired to survive a reboot.

- Package: `@cloudcli-ai/cloudcli` **v1.37.2**, installed as an npm
  global under nvm node `v22.23.2`
  (`~/.nvm/versions/node/v22.23.2/lib/node_modules/@cloudcli-ai/cloudcli`).
- Server process: **live**, `pid 3364070`, running since Sep 3
  (`dist-server/server/index.js`).
- Listening on `http://100.116.147.74:3001` — that's `bdrpisrvdev`'s
  **Tailscale** IP. `curl` returns **HTTP 200**.
- Reachable over Tailscale from your other tailnet devices
  (`bdotradslaptop`, `brads-s25-ultra`, `bdrpisrvami`). The `CloudCLI`
  Supabase project row points at `http://bdrpisrvdev:3001`, which is the
  same thing by hostname.
- Config: `~/.cloudcli/cloudcli.env` (HOST, SERVER_PORT, JWT_SECRET,
  CLAUDE_CLI_PATH, WORKSPACES_ROOT, DATABASE_PATH…).
- Login/account DB: `~/.cloudcli/auth.db` (SQLite, updated today).
- Runtime pointer: `~/.cloudcli/local-server.json`.

### Gaps

1. **No service manager.** It's a bare `node` process, not systemd. A
   reboot or a crash and it's gone — nothing brings it back.
2. **Not in the fleet.** There's a `CloudCLI` row in Supabase (with
   un-normalised free-text fields — see the Part C file) but no
   `~/projects/CloudCLI` dir, no request queue, no `_Instructions`
   copy. It's outside everything BdRDev orchestrates.
3. **No reverse proxy / TLS / friendly hostname** — it's raw
   `http://<tailscale-ip>:3001`.

## Questions before an unattended pass touches this

1. **Is `cloudcli` the tool you want to standardise on?** If yes, the
   work is "harden what's already there." If you meant something else
   (claude.ai/code web, a different self-hosted UI, etc.), say which and
   this becomes a fresh setup.

2. **Auto-start on boot** — do you want it made durable? Two ways, both
   no-sudo-for-me to write but I can't fully enable either alone:
   - a `systemd --user` unit + `loginctl enable-linger bdr` (the linger
     enable needs one `sudo` line from you), or
   - a system unit in `/etc/systemd/system/` (all sudo, you install it).
   Tell me which and I'll write the unit file and leave you the exact
   commands.

3. **Track it as its own project?** i.e. create `~/projects/CloudCLI/`
   with the standard `_Instructions/BdRDev.md` + `_Requests/` so future
   changes to it go through the normal request flow and it shows on the
   dashboard. Or leave it as an unmanaged standalone.

4. **Do you actually have a working login at `:3001` already?** If the
   pain point is "I can't get in" or "it can't find the `claude`
   binary," tell me the symptom and I'll debug that specifically —
   that's a concrete unattended-doable task.

5. **Reverse proxy?** Want nginx in front of it on `bdrpisrvdev` (e.g.
   `chat.bdrpisrvdev` / a path on the existing vhost) so it's not a
   bare port, or is `:3001` over Tailscale fine?

Flip line 1 to `READY` once you've answered enough of the above for a
pass to act.
