WAITING RESPONSE

Remove Other for software.
Add Tailscale
Add web linkk

---

## Picked up 2026-08-28 (Claude) — one thing to pin down first

Here's how I read the three asks. #1 and #2 are clear; #3 isn't.

### 1. "Remove Other for software" — clear

Drop the **Other** column from the Ecosystem 2 grid (the derived,
read-only one built from the free-text Software field). I'll also retire
the free-text "Software" box on the Fleet tab, since Other was its only
consumer — the Y/N package columns become the whole story. Say if you
want the free-text box kept for notes.

### 2. "Add Tailscale" — clear

Add **Tailscale** as a 5th Y/N software column (alongside Claude / Nginx
/ Supabase / SQL Lite), a checkbox on the Fleet tab, and a row in the
Supabase `software` catalogue + `server_software` seed. Defaults: on for
every current server (they're all on the tailnet).

### 3. "Add web link" — need one detail

Not sure what this attaches to. Which:

- **(a) A URL field on each *server*** — e.g. `https://bdrpiami.local`
  for the Pi — shown as a clickable link in the Ecosystem 2 grid
  (new column) and on the Fleet diagram. Servers have no web field
  today, only a bare `address` (IP).
- **(b) Make the existing app "Web address" clickable** — the Fleet
  diagram already shows it as a `🌐 …` chip; turn it into a real
  `<a href>` where it looks like a URL.
- **(c) Both.**
- **(d) Something else** — tell me where the link goes and what it
  points at.

??? --- Question --- ???

Which of (a) / (b) / (c) / (d) for "Add web link"? (Or just "a", etc.)

Also — this batch changes the Supabase schema seed (the Tailscale
catalogue row). Cleaner to land all of it in one go **with** the
Supabase activation from `rEditing Tables` so the SQL is run once. OK to
hold this until that's wired, or do you want the UI-only parts
(#1, #2 against the JSON fallback) shipped now regardless?

Answer:


??? --------------- ???
