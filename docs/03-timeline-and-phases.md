# UnderTheRock - Timeline and Phases

## Phased Rollout (PoC-First Approach)

### Phase 0: PoC (Months 1-2)
**Goal:** Tiger team validates architecture

- Probe IFWI Builder API vs. source builds
- Validate kernel CI integration
- Confirm integration with CI-Lite and TheRock
- **Architecture decision gate** → Phase 1 begins

### Phase 1: Foundation
- Repos setup
- LKG manifest creation
- SimNow pre-submit testing

### Phase 2: Hardware Pre-Submit
- Merge blocking enforced
- Target: <30 min feedback loop

### Phase 3: Nightly + LKG
- 18 builds per night
- LKG promotion with 83% quorum requirement

### Phase 4: Gardening
- Oncall rotation established
- Revert automation

### Phase 5: Traceability
- Release manifests
- Full matrix coverage

## Current Status (April 2026)

| Status | Item |
|--------|------|
| DONE | Architecture designed around theRock's three principles |
| DONE | Implementation plan complete (30K+ words) |
| DONE | Executive presentation ready (19 slides) |
| DONE | Super Build created and initial projects onboarded |
| IN PROGRESS | Tiger team surge on superbuild |

## Next Milestones for Tiger Team

1. Complete POC from source builds for all components of the IFWI
2. CI-Lite Integration
3. Kernel builds from source into UnderTheRock

## Key Documents

| Document | Location | Description |
|----------|----------|-------------|
| Executive Presentation | SharePoint (AIGROCm) | 19-slide overview of overall program |
| Implementation Plan | `under-the-rock/docs/current_draft_plan.md` | 30K+ word technical spec |
| MI450 BKC Modules | SharePoint spreadsheet | Component tracking for MI450 BKC |
| Firmware Integration Guide | `under-the-rock/docs/integrate-firmware-package-skill.md` | How to add your component to UnderTheRock |
