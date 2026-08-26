## What was done

Brad confirmed **BdRSrvAMI** is now real/reachable at `192.168.100.20`
(it's the renamed/repurposed `PlanBdRadServer` VM — already had real
work done on it per `_Instructions/SSH.md`: a deploy key installed and
BdRAMAssist's repo cloned there) and asked to add **BdRDev**'s own IP,
`192.168.100.10`, to the Ecosystem tab.

Verified `192.168.100.10` is this host's real LAN IP via `ip -4 addr
show` (`enp0s8`, matches the `192.168.100.0/24` subnet BdRSrvAMI is
also on) before using it.

Updated `app/templates/index.html`'s Ecosystem tab (both the graphical
fleet diagram and the ASCII tree below it):

- **BdRDev / BdRSrvDev**: replaced the `http://<pi-ip>:8420` placeholder
  address with `http://192.168.100.10:8420` in the fleet-diagram app
  card, and added the IP to the tree's server header
  (`BdRSrvDev  (this host, local, 192.168.100.10)`).
- **BdRSrvAMI**: switched its diagram card from a dashed "not
  provisioned yet" card to a solid one tagged `VM, 192.168.100.20`
  (dropped the `eco-server-planned`/`eco-tag-planned` classes), and
  added the IP to the tree header (`BdRSrvAMI  (VM, 192.168.100.20)`).
  Left `BdRSrvDungeon` marked not-provisioned — nothing indicates
  otherwise. Updated the "Not yet real" footnote under the tree to
  match: it no longer lists BdRSrvAMI as unprovisioned, notes it's the
  renamed `PlanBdRadServer` VM with BdRAMAssist's repo cloned there
  (not confirmed running as a deployed service yet), and confirms
  BdRSrvDev's real IP.

No backend/API changes — static reference content only, same as the
rest of the Ecosystem tab.

Verified live: force-restarted `bdrdev-dashboard` (`kill -9` on the
running PID, approved by Brad after the auto-mode classifier initially
declined it as a live-service restart — `debug=False`/no autoreload,
and SIGTERM doesn't trigger systemd's `Restart=on-failure`) and
confirmed via `curl localhost:8420/` that both new strings
(`192.168.100.10:8420` and `VM, 192.168.100.20`) are present in the
served HTML.

**Outcome:** implemented, deployed, and verified live.

## Original request (verbatim)

READY

BdRSrvAMI exists 192.168.100.20

Can you add the IP address to BdRDev 192.168.100.10
