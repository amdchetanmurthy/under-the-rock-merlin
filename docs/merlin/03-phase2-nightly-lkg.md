# Merlin Phase 2: Nightly Integration & LKG Promotion

**Depends on:** Phase 1 Foundation (pre-submit gate working for mi450)
**Goal:** 18 nightly builds across products and branches, automated LKG promotion, CI-Lite test execution.

---

## 1. Nightly Build Matrix (18 Builds)

From current_draft_plan.md — three groups of 6:

### Group A: ifwi/main × products (6 builds)

Build latest trunk of ALL firmware + latest kernel + latest ROCm.

| Build | IFWI Source | Kernel | ROCm | Product |
|-------|-----------|--------|------|---------|
| A1 | ifwi/main HEAD | LKG kernel | LKG ROCm | mi450 |
| A2 | ifwi/main HEAD | LKG kernel | LKG ROCm | mi455 |
| A3-A6 | ifwi/main HEAD | LKG kernel | LKG ROCm | Products TBD |

### Group B: firmware branches × products (6 builds)

Build production firmware branches (for shipping products).

| Build | IFWI Source | Kernel | ROCm | Product |
|-------|-----------|--------|------|---------|
| B1 | firmware-mi300x.B HEAD | LKG kernel | LKG ROCm | MI300X |
| B2-B6 | firmware-{product}.B HEAD | LKG kernel | LKG ROCm | Products TBD |

### Group C: theRock e2e × products (6 builds)

Full ROCm stack validation (coordinated with theRock team).

| Build | IFWI | Kernel | ROCm | Tests |
|-------|------|--------|------|-------|
| C1-C6 | LKG | LKG | Latest theRock | Runtime, math libs, frameworks, RCCL, perf |

---

## 2. Nightly Orchestrator Workflow

```yaml
# .github/workflows/merlin-nightly.yml
name: "Merlin Nightly"
on:
  schedule:
    - cron: '0 0 * * *'  # midnight UTC
  workflow_dispatch:
    inputs:
      force_promote:
        description: "Force LKG promotion even if quorum fails"
        type: boolean
        default: false

jobs:
  # ── Step 1: Resolve latest commits ──
  resolve:
    runs-on: ubuntu-latest
    outputs:
      ifwi_main_sha: ${{ steps.shas.outputs.ifwi_main }}
      kernel_sha: ${{ steps.shas.outputs.kernel }}
      rocm_sha: ${{ steps.shas.outputs.rocm }}
      date: ${{ steps.shas.outputs.date }}
    steps:
      - id: shas
        run: |
          # Resolve HEAD of each layer
          # In practice: git ls-remote to the actual repos
          echo "date=$(date -I)" >> $GITHUB_OUTPUT
          # ... resolve SHAs ...

  # ── Step 2A: Build trunk IFWI for each product ──
  build-trunk:
    needs: resolve
    strategy:
      matrix:
        product: [mi450]  # expand as products come online
      fail-fast: false
    runs-on: [self-hosted, undertherock-pool, ${{ matrix.product }}]
    steps:
      - uses: actions/checkout@v4
      - name: Full firmware build
        run: |
          source "${HOME}/venvs/uttr-conan/bin/activate"
          cmake -S . -B build -DUTTR_ASIC=${{ matrix.product }}
          ./scripts/firmware-all-with-report.sh build -- -j$(nproc)

      - name: Assemble IFWI image
        run: |
          python3 scripts/assemble-ifwi.py \
            --components build/output/ \
            --product ${{ matrix.product }} \
            --output build/ifwi-${{ matrix.product }}.bin

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: nightly-ifwi-trunk-${{ matrix.product }}
          path: |
            build/ifwi-${{ matrix.product }}.bin
            build/output/

  # ── Step 2B: SimNow + Hardware tests ──
  test-trunk:
    needs: [resolve, build-trunk]
    strategy:
      matrix:
        product: [mi450]
      fail-fast: false
    runs-on: [self-hosted, simnow, ${{ matrix.product }}]
    steps:
      - name: Download IFWI
        uses: actions/download-artifact@v4
        with:
          name: nightly-ifwi-trunk-${{ matrix.product }}

      - name: Run extended test suite
        run: |
          python3 scripts/merlin-test-runner.py \
            --product ${{ matrix.product }} \
            --ifwi ifwi-${{ matrix.product }}.bin \
            --suite nightly \
            --timeout 14400 \
            --junit-xml results/nightly-${{ matrix.product }}.xml

  # ── Step 3: LKG Promotion ──
  promote-lkg:
    needs: [resolve, test-trunk]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - uses: actions/checkout@v4

      - name: Evaluate quorum
        id: quorum
        run: |
          # Count passed builds
          # Quorum: 15/18 (83%)
          # Initially with fewer products: adjust threshold proportionally
          # e.g., 1 product = 1/1 must pass
          total=${{ strategy.job-total }}
          passed=$(echo '${{ toJSON(needs.test-trunk.result) }}' | jq '[.[] | select(. == "success")] | length')
          threshold=$(echo "$total * 83 / 100" | bc)

          echo "total=$total" >> $GITHUB_OUTPUT
          echo "passed=$passed" >> $GITHUB_OUTPUT
          echo "threshold=$threshold" >> $GITHUB_OUTPUT

          if [ "$passed" -ge "$threshold" ] || [ "${{ inputs.force_promote }}" == "true" ]; then
            echo "decision=PROMOTE" >> $GITHUB_OUTPUT
          else
            echo "decision=GARDENING" >> $GITHUB_OUTPUT
          fi

      - name: Update LKG manifest
        if: steps.quorum.outputs.decision == 'PROMOTE'
        run: |
          python3 scripts/update-lkg-manifest.py \
            --date ${{ needs.resolve.outputs.date }} \
            --ifwi-sha ${{ needs.resolve.outputs.ifwi_main_sha }} \
            --kernel-sha ${{ needs.resolve.outputs.kernel_sha }} \
            --rocm-sha ${{ needs.resolve.outputs.rocm_sha }} \
            --passed ${{ steps.quorum.outputs.passed }} \
            --total ${{ steps.quorum.outputs.total }}

          git add lkg-manifest.yaml
          git commit -m "Promote LKG: ${{ needs.resolve.outputs.date }}"
          git push

      - name: Upload component binaries to LKG cache
        if: steps.quorum.outputs.decision == 'PROMOTE'
        run: |
          date=${{ needs.resolve.outputs.date }}
          for component in build/output/*/; do
            name=$(basename "$component")
            jfrog rt upload \
              "${component}/*" \
              "uttr-lkg/${date}/components/${name}/"
          done

      - name: Create gardening issue on failure
        if: steps.quorum.outputs.decision == 'GARDENING'
        uses: actions/github-script@v7
        with:
          script: |
            // Create P0 issue, assign gardeners, trigger bisection
            // See current_draft_plan.md lines 1352-1398 for template
```

---

## 3. CI-Lite Integration

Once nightly builds produce validated IFWI images, they feed into **CI-Lite** infrastructure for extended rack-level testing.

```
Nightly Build Output
    │
    ├── IFWI binary (per product)
    ├── Kernel package
    ├── ROCm package
    │
    ▼
┌──────────────────────────────────────────────────┐
│ CI-LITE INFRASTRUCTURE                            │
│                                                    │
│  Consumes nightly artifacts                        │
│  Runs rack-level tests:                            │
│    - Multi-GPU topology validation                 │
│    - IFoE fabric mesh tests                        │
│    - Power/thermal cycling                         │
│    - Customer workload simulation                  │
│    - Full RVS (ROCm Validation Suite)              │
│                                                    │
│  Reports results back to Merlin for LKG decision   │
└──────────────────────────────────────────────────┘
```

---

## 4. Gardener Rotation

### 4.1 Roles (from current_draft_plan.md)

| Gardener | Scope | Oncall Period | Pool Size |
|----------|-------|---------------|-----------|
| IFWI Gardener | PSP, MPIO, PMFW, RAS, UMC, VBL | Weekly | 6-8 IFWI TLs |
| Kernel Gardener | amdgpu driver | Weekly | 6-8 kernel TLs |
| ROCm Gardener | Runtime, libraries, frameworks | Weekly | Already exists (RFC0002) |
| Rack Integration Gardener | MI450 rack-level, cross-layer | Weekly | 6-8 rack TLs |

### 4.2 Gardener SLA

- **4 hours** to revert or fix from nightly failure notification
- **Revert first** — don't debug in place
- **LKG promotion authority** — gardeners collectively approve/reject

### 4.3 Triage Flow

```
Nightly fails (< 15/18 quorum)
    │
    ▼
GitHub issue created (P0, label: gardening)
    │
    ├── Assigned to: @ifwi-oncall, @kernel-oncall, @rocm-oncall
    │
    ├── Auto-bisection triggered (if feasible)
    │
    ▼
Gardener investigates:
    ├── Read test-result.yaml → identify failing assertion
    ├── git log → find commits since last good LKG
    ├── AI triage agent suggests suspect commits (Phase 6)
    │
    ▼
Decision:
    ├── Revert suspect commit → trunk green → next nightly promotes
    └── Fix available → merge fix → next nightly validates
```

---

## 5. Phase 2 Milestone Checklist

```
□ Nightly orchestrator workflow running daily
□ Build-trunk produces IFWI images for mi450
□ SimNow extended test suite (boot, reset, enumeration, driver, RVS subset)
□ LKG promotion logic implemented (quorum-based)
□ lkg-manifest.yaml auto-updated on promotion
□ LKG component binaries uploaded to Artifactory
□ Gardener issue creation on quorum failure
□ Historical LKG snapshots preserved (lkg-manifests/ directory)
□ CI-Lite receives nightly artifacts (integration point defined)
□ Pre-submit gate uses LKG cache (from Phase 1) backed by real nightly LKGs
□ Dashboard: nightly pass rates, LKG freshness, gardener response time
```
