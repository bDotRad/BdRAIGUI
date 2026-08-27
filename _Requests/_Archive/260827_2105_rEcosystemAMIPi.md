## What was done

Brad reported the AMI server has changed: it's no longer the
`PlanBdRadServer` VM but a physical **Raspberry Pi 8GB**, renamed
**BdRPiAMI**, at **10.10.10.20** (was `BdRSrvAMI` / `192.168.100.20`).

Scope confirmed with Brad: **Ecosystem tab only** for now. `SSH.md` and
`AppServerSync.md` still refer to `BdRSrvAMI` / `192.168.100.20` and
were deliberately left as-is (historical deploy-key / app-sync records);
`BdRSrvDev` stays at `192.168.100.10` — the two machines are now on
different subnets, which Brad is aware of.

Updated `app/templates/index.html`'s Ecosystem tab in three places:

- **Fleet diagram card**: `BdRSrvAMI` → `BdRPiAMI`, tag
  `VM, 192.168.100.20` → `Raspberry Pi 8GB, 10.10.10.20`, specs pill
  `Ubuntu Server · 8GB RAM · 256GB SSD` → `Raspberry Pi · 8GB RAM`
  (storage unknown, left out), and the PlanBdRad app card's address
  chip `192.168.100.20` → `10.10.10.20`.
- **ASCII tree**: header `BdRSrvAMI  (VM, 192.168.100.20)` →
  `BdRPiAMI  (Raspberry Pi 8GB, 10.10.10.20)`, Specs line updated to
  match.
- **"Not yet real" footnote**: reworded from "the renamed/repurposed
  `PlanBdRadServer` VM, 192.168.100.20" to "formerly the
  `PlanBdRadServer` VM; now a physical Raspberry Pi 8GB at 10.10.10.20".

Static reference content only — no backend/API changes.

Verified live: force-restarted `bdrdev-dashboard` (`kill -9` on PID
1090; `debug=False`/no autoreload, SIGTERM doesn't trigger systemd's
`Restart=on-failure`), waited for the service to come back `active`,
and confirmed via `curl localhost:8420/` that the served HTML now
contains `BdRPiAMI` / `Raspberry Pi 8GB, 10.10.10.20` / `10.10.10.20`
and no longer contains `BdRSrvAMI` or `192.168.100.20`.

**Outcome:** implemented, deployed, and verified live.

## Original request (verbatim)

READY

Update the ecosystem so that the AMI server is now a Raspberry Pi 8GB

It is
BdRPiAMI
10.10.10.20
