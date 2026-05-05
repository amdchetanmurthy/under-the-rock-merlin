# UnderTheRock - Project Overview

## What Is UnderTheRock?

UnderTheRock is an AMD initiative to apply **theRock's three principles** to firmware (IFWI) and kernel driver (amdgpu) development, making the complete GPU stack as simple to develop as ROCm alone. It aligns firmware and kernel development with theRock's direction for ROCm 7.0+.

### The Three Principles (from theRock)

1. **Trunk is Shippable** — Pre-submit gates, revert-first culture, nightly LKG promotion
2. **Simplified Codebase** — GitHub consolidation, one CI platform, unified workflows
3. **Consistent, Comprehensive, Reproducible Releases** — Manifest-driven BKC, 18x test coverage, full traceability

**Result:** One unified platform where firmware, kernel, and ROCm developers work the same way.

## The Problem Being Solved

### Today's Reality
- **Fragmented tooling** — IFWI, kernel, ROCm use different tools, workflows, infrastructure
- **Trunk frequently broken** — No pre-submit testing; regressions sit undetected 24-48 hours
- **No shared baseline** — Developers guess which I×K×R (IFWI × Kernel × ROCm) combinations work together
- **QA-driven triage** — Developers brought in reactively days after committing

### Business Impact
- Customer field failures from untested I×K×R combinations
- Extended debug cycles
- Lost developer productivity
- Quality concerns

### UnderTheRock Solution
Developer simplicity through automation, pre-submit gates (<30 min feedback), nightly LKG promotion, and complete stack validation.

## Key Benefits

| Metric | Today | UnderTheRock | Improvement |
|--------|-------|-------------|-------------|
| Regression detection | 24-48 hours | <30 minutes | 96% faster |
| Trunk stability | Frequently broken | Always usable | 100% uptime |
| Test coverage | 1 I×K×R combo/week | 18 builds/night | 18x coverage |
| Pre-submit testing | None (IFWI/kernel) | 100% of commits | New capability |
| CI platforms | 3 systems | 1 system (GHA) | 67% reduction |

### Developer Experience Target
> "I open a PR. Within 30 minutes I know if my change is safe to merge. Trunk always works. LKG manifest tells me which versions work together. Zero friction."

## Relationship to theRock

- **theRock** = ROCm (userspace). Open source: https://github.com/rocm/therock
- **UnderTheRock** = IFWI + kernel (firmware + driver)
- Tightly integrated via **shared LKG promotion**
  - Joint nightly decision: All 18 nightlies contribute to LKG quorum
  - Single `lkg-manifest.yaml` contains IFWI + kernel + ROCm SHAs
  - Coordinated gardening: IFWI, kernel, ROCm gardeners collaborate

## Relationship to DPEG's Rack Testing

UnderTheRock provides **candidate E2E BKC** (rack SW-FW recipe) to DPEG. DPEG performs extended rack-level validation. Feedback loop declares LKG.

## NPI (Confidential Products)

Closed `npi-{product}` repos/branches. At launch, updatable firmware upstreams to main. ROM stays closed.

## Contact

- **Email distro:** UnderTheRock.Core@amd.com
- **Project lead:** Chris Sosa
- **Short URL:** https://u.amd.com/under-the-rock
- **Confluence:** https://amd.atlassian.net/wiki/spaces/SHARK/pages/1600726439/Project+UnderTheRock
