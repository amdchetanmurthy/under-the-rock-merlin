# Merlin Phase 0: Proof of Concept

**Goal:** Prove end-to-end that a PR to one firmware component can be automatically built, assembled into an IFWI image, tested on SimNow, and reported back to the PR — all within 30 minutes.

---

## PoC Scope

**One component, one product, one gate.**

| Dimension | PoC Choice | Why |
|-----------|-----------|-----|
| Component | fw-asp-fmc | Most mature build (Conan + Make), well-documented IVV workflow (aspfmc-build-sign.yml), produces PSP entry 0x1 (128K) |
| Product | mi450 | Primary UnderTheRock target, CMakePresets.json already defines mi450 preset |
| SimNow test | Boot validation only (L0) | Minimal viable test — IFWI boots to PSP ready state |
| Runner | Existing IVV self-hosted runner | Already has NFS mounts, Conan venv, Xtensa tools |

## PoC Decision Point

The PoC answers one critical question from current_draft_plan.md:

> **IFWI build approach: Option A (IFWI Builder API) or Option B (source builds)?**

| Option | Approach | PoC Test |
|--------|----------|----------|
| A | Call IFWI Builder at `http://rocm-ci.amd.com/` with PR's asp-fmc binary + LKG binaries for everything else → get assembled SPIROM | Can we call the API from GHA? What's the latency? |
| B | Build all 74 PSP entries from source using the CMake meta-build, then assemble SPIROM ourselves | Can we assemble a valid image? Build time? |

**PoC deliverable:** Working GHA workflow for ONE option (likely A, since IFWI Builder already exists).

---

## PoC Implementation Plan

### Step 1: Build + Assembly

#### 1a: GHA Workflow Skeleton

Create `.github/workflows/merlin-presubmit-poc.yml`:

```yaml
name: "Merlin Pre-Submit PoC"
on:
  pull_request:
    paths:
      - 'firmware/asp-fmc/**'
      - 'patches/asp-fmc/**'
  workflow_dispatch:  # manual trigger for testing

jobs:
  build-asp-fmc:
    runs-on: [self-hosted, undertherock-pool]
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: false

      - name: Fetch asp-fmc sources
        run: |
          python3 build_tools/fetch_sources.py \
            --skip-failed \
            --shallow-firmware-driver

      - name: Build fw-asp-fmc
        run: |
          source "${HOME}/venvs/uttr-conan/bin/activate"
          cmake --preset mi450
          cmake --build build --target fw-asp-fmc -j$(nproc)

      - name: Verify build output
        run: |
          test -d build/output/asp-fmc/ || exit 1
          ls -la build/output/asp-fmc/
          echo "asp-fmc binary built successfully"

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: asp-fmc-binary
          path: build/output/asp-fmc/
```

**Validation:** This workflow must produce `build/output/asp-fmc/` with the MPASP_FMC binary.

#### 1b: IFWI Assembly (Option A)

Investigate and implement IFWI Builder API call:

```bash
# Pseudocode — actual API TBD with IFWI team
# 1. Fetch LKG IFWI image (complete, known-good)
curl -o lkg-ifwi.bin "artifactory://uttr-lkg/latest/ifwi-mi450.bin"

# 2. Extract individual PSP entries from LKG image
# (or maintain a per-entry LKG cache in Artifactory)

# 3. Replace entry 0x1 (MPASP_FMC) with PR's build output
# Option A: Call IFWI Builder API
curl -X POST http://rocm-ci.amd.com/api/assemble \
  -F "base_image=@lkg-ifwi.bin" \
  -F "override_0x0001=@build/output/asp-fmc/mpasp_fmc.bin" \
  -F "product=mi450" \
  -o assembled-ifwi.bin

# Option B: Binary patching (replace bytes at PSP directory offset)
# This requires understanding L2 PSP directory entry offsets
# PSP entry 0x1 (MPASP_FMC) is at L2PspDirectoryTable index 18
# Location in SPIROM = directory entry's Location field
```

**Key questions to resolve with IFWI team:**
1. Does IFWI Builder have an API? Or is it GUI-only?
2. Can we submit individual binary replacements, or must we provide all 74 entries?
3. What signing is required? (fw-asp-fmc sets `UTTR_MPIO_SKIP_SIGN=ON` locally)
4. Latency of assembly API call?

**Fallback (Option B alternative):** If no API exists, build a Python script that:
1. Reads the LKG IFWI SPIROM image (8MB)
2. Parses L2 PSP Directory at offset 0x020000
3. Finds entry type 0x1 (MPASP_FMC) → gets its Location and Size
4. Replaces the binary at that Location with the PR's build output
5. Recalculates L2 PSP Directory checksum
6. Writes the modified SPIROM image

This is feasible because the PSP directory structure is well-documented (see memory-bank/14-ifwi-layout-mi450.md).

#### 1c: LKG Binary Bootstrap

Create initial LKG state:

```bash
# Build all components from trunk HEAD
source "${HOME}/venvs/uttr-conan/bin/activate"
cmake --preset mi450
cmake --build build --target firmware-all -j$(nproc)

# Upload each component's output to Artifactory as "LKG v0"
for component in build/output/*/; do
  name=$(basename "$component")
  jfrog rt upload \
    "${component}/*" \
    "uttr-lkg/bootstrap/${name}/"
done

# Create initial lkg-manifest.yaml
cat > lkg-manifest.yaml << 'EOF'
date: "2026-05-05"
promoted_at: "2026-05-05T00:00:00Z"
bootstrap: true
note: "Initial LKG from trunk HEAD, not yet validated by nightly"

components:
  asp-fmc:
    commit: $(git -C firmware/asp-fmc rev-parse HEAD)
    artifact: "artifactory://uttr-lkg/bootstrap/asp-fmc/"
  # ... repeat for each component
EOF
```

### Step 2: SimNow + Reporting

#### 2a: SimNow Integration

Add SimNow test job to the workflow:

```yaml
  simnow-boot-test:
    needs: build-asp-fmc
    runs-on: [self-hosted, simnow, mi450]
    steps:
      - name: Download assembled IFWI
        uses: actions/download-artifact@v4
        with:
          name: assembled-ifwi

      - name: Run SimNow boot test
        id: simnow
        run: |
          # SimNow invocation (exact CLI TBD with SimNow team)
          # Reference: IVV uses simnow in patch-run-simnow.yml
          simnow \
            --config configs/mi450_a0.cfg \
            --load-ifwi assembled-ifwi.bin \
            --test boot \
            --timeout 300 \
            --log simnow-boot.log \
            2>&1 | tee simnow-output.txt

          # Check for successful boot markers
          if grep -q "PSP firmware initialized" simnow-output.txt && \
             grep -q "GPU enumerated" simnow-output.txt; then
            echo "result=PASS" >> $GITHUB_OUTPUT
          else
            echo "result=FAIL" >> $GITHUB_OUTPUT
          fi

      - name: Generate JUnit XML
        if: always()
        run: |
          python3 scripts/simnow-to-junit.py \
            --input simnow-output.txt \
            --output simnow-results.xml \
            --test-name "L0_boot" \
            --result ${{ steps.simnow.outputs.result }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: simnow-results
          path: |
            simnow-results.xml
            simnow-boot.log
```

#### 2b: Result Reporting

```yaml
  report:
    needs: [build-asp-fmc, simnow-boot-test]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Download results
        uses: actions/download-artifact@v4
        with:
          name: simnow-results

      - name: Publish results to PR
        uses: dorny/test-reporter@v1
        with:
          name: "Merlin Gate: SimNow Boot (mi450)"
          path: simnow-results.xml
          reporter: java-junit
          fail-on-error: true
```

#### 2c: End-to-End Validation

1. Create a test PR that modifies `firmware/asp-fmc/` (e.g., bump a version string)
2. Verify the full pipeline runs: build → assembly → SimNow → report
3. Verify PR shows pass/fail check
4. Measure total wall-clock time (target: < 30 min)
5. Document blockers and findings

---

## PoC Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Build succeeds | fw-asp-fmc produces binary | Binary in build/output/asp-fmc/ |
| IFWI assembles | Valid 8MB SPIROM image | Image loads in SimNow without parse errors |
| SimNow boots | PSP initializes, GPU enumerates | Boot log shows expected markers |
| PR gets result | GitHub Check posted | Pass/fail visible on PR within 30 min |
| Total duration | Wall clock from PR open to result | < 30 minutes |

## PoC Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| IFWI Builder has no API | Can't assemble image automatically | Write Python SPIROM assembler using L2 PSP directory knowledge |
| SimNow not available on GHA runners | Can't run boot test | Use existing IVV SimNow runners, request access |
| Conan packages unavailable from GHA | Build fails on dependency fetch | Pre-cache Conan packages on IVV runner image |
| Unsigned binary rejected by SimNow | Boot fails at PSP verification | Use debug/unsigned SimNow mode, or implement signing |
| NFS mounts not available | Xtensa/CBWA tools missing | Use IVV runners that already have mounts |
| Total time exceeds 30 min | Gate too slow for developer adoption | Profile each phase, parallelize where possible |

## PoC Deliverables

1. **Working GHA workflow** (`.github/workflows/merlin-presubmit-poc.yml`)
2. **IFWI assembly script or API integration** (`scripts/assemble-ifwi.py` or API wrapper)
3. **SimNow test harness** (`scripts/simnow-to-junit.py`)
4. **Bootstrap LKG manifest** (`lkg-manifest.yaml`)
5. **Decision document:** Option A vs Option B for IFWI assembly
6. **Timing breakdown:** Build (X min) + Assembly (X min) + SimNow (X min) + Report (X min)
