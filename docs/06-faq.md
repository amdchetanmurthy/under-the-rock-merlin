# UnderTheRock - FAQ

## Q: Why not just improve the existing BKC process?
**A:** BKC tests one combination weekly. UnderTheRock needs 18 nightly builds + pre-submit gates for all commits. This requires a new development model and infrastructure — incremental improvements to the existing process won't get there.

## Q: Will pre-submit testing slow developers down?
**A:** No. A 30-minute gate is faster than debugging broken trunk for hours/days. Net positive for velocity.

## Q: How does UnderTheRock relate to theRock?
**A:** theRock = ROCm (userspace). UnderTheRock = IFWI + kernel (firmware + driver). They are tightly integrated via shared LKG promotion using a single `lkg-manifest.yaml`.

## Q: What's the relationship to DPEG's rack testing?
**A:** UnderTheRock provides **candidate E2E BKC** (rack SW-FW recipe) to DPEG. DPEG performs extended rack-level validation. The feedback loop declares LKG.

## Q: What about NPI (confidential products)?
**A:** Closed `npi-{product}` repos/branches. At launch, updatable firmware upstreams to main. ROM stays closed.

## Q: Is this just for ROCm developers?
**A:** No — this is primarily for **IFWI firmware engineers** and **kernel driver engineers**. ROCm already has theRock.

## Q: What's the difference between the UnderTheRock program and the Installer?
**A:** The UnderTheRock program is about _building_ firmware from source (super-build, LKG promotion, CI gates). The installer is about _deploying_ validated BKC stacks to hardware.

## Q: What hardware does the Installer target?
**A:** MI455X Helios compute trays. v0 targets a single compute tray, v2 will orchestrate across 8 compute trays per rack.

## Q: What are the default BMC credentials?
**A:** Username: `root`, Password: `0penBmc`. AMC internal IP: `192.168.31.1`.
