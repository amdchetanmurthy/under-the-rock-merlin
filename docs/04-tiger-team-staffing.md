# UnderTheRock - Tiger Team and Staffing

## Current Team Allocation (as of April 2026)

### Chris Sosa (Project Lead)
- **Build system**: 99% of time — can swap to CI if someone takes build
- **Dev machines**: ~1% — blocking new task force members

### Eric
- **FW recipes**: 100% full-time

### Pirabu Panchadcharam
- **Dev machines**: max 40% / 2 days per week

## Critical Staffing Gaps

### 1. CI Infrastructure Owner (Full-time, URGENT)

**The situation:** Chris currently owns the build system and can swap to CI, but can't do both.

**What they'd do:**
- Partner immediately with Prashant to get the nightly CI-lite work stood up
- Pull in UnderTheRock once building IFWI
- Work with IT on GitHub Actions runner provisioning (permissions, NFS mounts, signing tools)
- Coordinate infrastructure with TheRock team
  - NOTE: TheRock's existing builders won't work for UnderTheRock
  - Can't immediately extend Ivo's team infrastructure (they've made choices that require rework)
- Ideally set up in AWS to align with TheRock's direction

**Risk:** Without this, there is no one to build any CI for UnderTheRock until the super build is done or has another owner.

### 2. Full-Time IC for Firmware Build Recipes

**The situation:** Need to iterate through all ~65 firmware build recipes and get them into the super-build.

**What they'd do:**
- Reverse engineer existing firmware builds (~65 components)
- Convert recipes into super-build compatible format (AI-assisted with Cursor/Claude)
- Handle package dependencies, host dependencies, toolchain setup
- The more opinionated this person is about handling packages and host dependencies, the better

**Risk:** Volume — too many recipes for Chris to iterate through while also handling build system architecture.

### 3. Part-Time (25-50%) Repo Mapping & Automation

**The situation:** Need to figure out all the other repos and set up small automation for dependency rolls.

**What they'd do:**
- Map remaining firmware repositories
- Small automation for dependency roll-ups (submodule updates, version bumps)
- Git submodule expertise for super-repo architecture

**Risk:** Coordination overhead — 65+ repos need ongoing dependency management.

### 4. Developer Machines Owner

**The situation:** Chris worked with PFO team to get his own Ubuntu machine, but it's not replicable because PFO is running out of Azure quota.

**What they'd do:**
- Set up replicable developer machines for tiger team
- Solve Azure quota issues (or find alternative)
- Ensure firewall + AMD network access
- Document setup for future team members

**Risk:** New team members are blocked from starting without a working dev environment.

## Impact Without Staffing

Without help on these four areas:
- **PoC slips 3-6 months**
- **Cannot integrate with CI-lite**

## How to Help
- Reach out to **Chris Sosa** directly
- Even part-time or loaned help would be valuable
- Roles #1, #3, and #4 are most urgent (Week 1)
