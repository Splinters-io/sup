# sup — Supply Chain Quarantine

**A time-based trust gate for your dependencies.**

`sup` refuses to let your project consume a dependency version until it has existed in its registry for a configurable number of days. The premise is simple: most supply chain attacks are discovered within days of publication. If you aren't the first to install a compromised package, you probably won't be a victim.

## The idea

Software supply chain attacks share a common lifecycle:

1. Attacker publishes a malicious package (or hijacks an existing one)
2. Automated pipelines pull it immediately — `npm install`, `pip install`, CI/CD
3. Hours to days later, the community notices and the package is yanked

The window between steps 1 and 3 is where damage happens. `sup` closes that window by enforcing a **quarantine period**: a version must have been published for N days before your project is allowed to depend on it.

This is not a silver bullet. It won't catch:
- Attacks that go undetected for months
- Compromised maintainer accounts where the malicious code looks legitimate
- Vulnerabilities (as opposed to intentional malice) — use `pip-audit`, `npm audit`, Snyk for those

What it **does** do is remove you from the blast radius of the most common attack pattern: the smash-and-grab, where a poisoned version exists for hours or days before being reported and pulled. That pattern accounts for a significant share of real-world incidents (event-stream, ua-parser-js, colors.js, node-ipc, etc.).

Think of it as one sensible player on the pitch, not the entire team.

## Two tiers

| Tier | Default | Intended use |
|------|---------|--------------|
| **Known** | 10 days | Standard projects — enough time for the community to surface problems |
| **Bleeding Edge** | 14 days | Higher-risk environments — two-week buffer before any new version is trusted |

Both thresholds are configurable. Some teams will want 3 days. Some will want 30. The defaults are a starting point.

## Install

```bash
pip install .
# or for development:
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Usage

```bash
# Scan your project (auto-detects ecosystem)
sup check

# Scan with a specific tier
sup check --tier bleeding_edge

# Warn but don't block (exit 0 regardless)
sup check --warn-only

# Force a specific ecosystem
sup check --type node

# Check a specific package
sup info requests --registry pypi --version 2.31.0

# Set up your config file
sup config --init
sup config --show

# Check an SBOM (CycloneDX or SPDX JSON)
sup sbom check path/to/sbom.json

# Enrich an SBOM with quarantine annotations
sup sbom enrich path/to/sbom.json -o enriched.json
sup sbom enrich path/to/sbom.json --tier bleeding_edge
```

### In CI

```yaml
# GitHub Actions example
- name: Supply chain quarantine check
  run: sup check
```

`sup check` exits 1 when any dependency is still in quarantine. Use `--warn-only` during rollout to surface issues without blocking builds.

## Supported ecosystems

| Ecosystem | Files parsed | Registry queried |
|-----------|-------------|-----------------|
| Python | `requirements.txt`, `pyproject.toml`, `poetry.lock`, `Pipfile.lock` | PyPI |
| Node.js | `package.json`, `package-lock.json`, `yarn.lock` | npm |
| Go | `go.mod` | proxy.golang.org |
| Rust | `Cargo.toml`, `Cargo.lock` | crates.io |
| Ruby | `Gemfile.lock` | RubyGems |

## SBOM support

`sup` can ingest, check, and enrich SBOMs in both major formats:

| Format | Spec | Input | Output |
|--------|------|-------|--------|
| **CycloneDX** | 1.5 JSON | `sup sbom check` | `sup sbom enrich` adds `sup:quarantine:*` properties to components |
| **SPDX** | 2.3 JSON | `sup sbom check` | `sup sbom enrich` adds REVIEW annotations to packages |

Packages are identified by **Package URL (purl)** — `pkg:pypi/requests@2.31.0`, `pkg:npm/express@4.18.2`, etc. — which maps directly to the 5 supported ecosystems.

**Enriched CycloneDX** adds properties to each component:
```json
{
  "name": "sup:quarantine:status", "value": "safe"
},
{
  "name": "sup:quarantine:age_days", "value": "1043"
},
{
  "name": "sup:quarantine:publish_date", "value": "2023-05-22T15:12:42Z"
}
```

**Enriched SPDX** adds annotations:
```
sup-quarantine: status=safe, age=1043d, published=2023-05-22, tier=known, threshold=10d
```

Both formats also record `sup-quarantine` as a tool in the SBOM metadata, so downstream consumers know the SBOM has been quarantine-checked.

## Proof of functionality

All tests below were run live against real package registries on 2026-03-31.

### All ecosystems resolve publish dates correctly

```
=== PYTHON (PyPI) ===
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Package  ┃ Version ┃   Age ┃ Status ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ requests │ 2.31.0  │ 1043d │ safe   │
│ flask    │ 3.0.0   │  912d │ safe   │
│ click    │ 8.1.7   │  956d │ safe   │
└──────────┴─────────┴───────┴────────┘
All packages have passed quarantine.  EXIT: 0

=== NODE (npm) ===
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Package ┃ Version ┃   Age ┃ Status ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ express │ 4.18.2  │ 1269d │ safe   │
│ lodash  │ 4.17.21 │ 1864d │ safe   │
└─────────┴─────────┴───────┴────────┘
All packages have passed quarantine.  EXIT: 0

=== GO (proxy.golang.org) ===
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Package                     ┃ Version ┃   Age ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ github.com/gin-gonic/gin    │ v1.9.1  │ 1034d │ safe   │
│ github.com/stretchr/testify │ v1.8.4  │ 1035d │ safe   │
└─────────────────────────────┴─────────┴───────┴────────┘
All packages have passed quarantine.  EXIT: 0

=== RUST (crates.io) ===
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━━┓
┃ Package ┃ Version ┃  Age ┃ Status ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━━┩
│ serde   │ 1.0.197 │ 770d │ safe   │
│ tokio   │ 1.36.0  │ 787d │ safe   │
└─────────┴─────────┴──────┴────────┘
All packages have passed quarantine.  EXIT: 0

=== RUBY (RubyGems) ===
┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Package ┃ Version ┃   Age ┃ Status ┃
┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ rack    │ 3.0.8   │ 1021d │ safe   │
│ rails   │ 7.1.2   │  871d │ safe   │
└─────────┴─────────┴───────┴────────┘
All packages have passed quarantine.  EXIT: 0
```

### Quarantine blocking works

When the threshold exceeds a package's age, `sup` blocks with exit code 1:

```
=== QUARANTINE BLOCK (threshold: 2000 days) ===
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package  ┃ Version ┃   Age ┃ Status                        ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ requests │ 2.31.0  │ 1043d │ QUARANTINE (until 2028-11-11) │
│ flask    │ 3.0.0   │  912d │ QUARANTINE (until 2029-03-22) │
│ click    │ 8.1.7   │  956d │ QUARANTINE (until 2029-02-06) │
└──────────┴─────────┴───────┴───────────────────────────────┘
Blocked: 3 package(s) in quarantine.  EXIT: 1
```

### Warn-only mode exits clean

Same quarantine situation, but with `--warn-only` the exit code is 0 — safe for gradual rollout:

```
=== WARN-ONLY MODE ===
Warning: 3 package(s) in quarantine.  EXIT: 0
```

### SBOM check works across ecosystems in a single file

A CycloneDX SBOM containing Python, Node, Rust, Go, and Ruby components — all resolved via purl:

```
=== SBOM CHECK (CycloneDX, live) ===
Parsed cyclonedx SBOM: 6 components
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Component                ┃ Version ┃ Ecosystem ┃   Age ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ requests                 │ 2.31.0  │ python    │ 1043d │ safe   │
│ flask                    │ 3.0.0   │ python    │  912d │ safe   │
│ express                  │ 4.18.2  │ node      │ 1269d │ safe   │
│ serde                    │ 1.0.197 │ rust      │  770d │ safe   │
│ github.com/gin-gonic/gin │ v1.9.1  │ go        │ 1034d │ safe   │
│ rails                    │ 7.1.2   │ ruby      │  871d │ safe   │
└──────────────────────────┴─────────┴───────────┴───────┴────────┘
All SBOM components have passed quarantine.  EXIT: 0
```

### SBOM enrichment embeds quarantine metadata

```
sup sbom enrich sbom-cyclonedx.json -o enriched.json

→ Component "requests" gets properties:
    sup:quarantine:status:       safe
    sup:quarantine:age_days:     1043
    sup:quarantine:publish_date: 2023-05-22T15:12:42Z
    sup:quarantine:tier:         known
    sup:quarantine:threshold_days: 10

→ Metadata records: Tool: sup-quarantine v0.1.0
```

## Configuration

Config lives at `~/.config/sup/config.toml`:

```toml
[tiers]
known = 10           # days
bleeding_edge = 14

[behavior]
default_tier = "known"
warn_only = false

[registries]
# Uncomment to use private registries
# pypi = "https://private.pypi.org"
# npm = "https://private.npmjs.org"
```

## Known limitations

- **npm**: The npm registry [dropped the `time` field](https://github.blog/changelog/2021-03-05-packages-time-has-been-dropped-from-npm-package-metadata-responses/) from metadata responses in March 2021. It may be absent for some packages. `sup` handles this gracefully but cannot determine ages when the data is missing.
- **Go proxy**: Timestamps reflect when a version was first cached by `proxy.golang.org`, not the original release time.
- **Version ranges**: `sup` works best with lockfiles that pin exact versions. Manifest files with ranges (e.g., `>=1.0,<2`) will resolve to the lower bound, which may not match a real registry release.
- **Private registries**: Supported via config, but each registry must expose publish dates in the same format as its public counterpart.

## Where it fits

```
┌─────────────────────────────────────────────────────┐
│                Your dependency pipeline              │
│                                                      │
│  1. sup check         ← age gate (this tool)        │
│  2. pip-audit / npm audit  ← known vulnerabilities  │
│  3. socket.dev / snyk      ← malware detection      │
│  4. license check          ← legal compliance       │
│  5. pin + lock             ← reproducibility        │
└─────────────────────────────────────────────────────┘
```

`sup` is layer 1 — the cheapest, fastest check. It adds seconds to your pipeline and catches the class of attack where speed is the attacker's primary weapon.

## Test suite

```bash
# Run all 83 tests
pytest

# With coverage (93%)
pytest --cov=sup --cov-report=term-missing
```

## License

MIT
