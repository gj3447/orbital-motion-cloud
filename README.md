# Orbital Motion Cloud

Position 8 apostle module. This repository preserves the source-attested identity and English label. The user's 2026-10-10 assignment adds hardware-adaptive data placement as one OMC function; the local implementation is a bounded CLI, with the original identity and source archive preserved.

Identity and source pins are in `APOSTLE_MODULE.json`. The dashboard owner is [METAHUMOTONIC_DASHBOARD](https://github.com/gj3447/METAHUMOTONIC_DASHBOARD); its `graph/apostles.json` records the roster selection.

```sh
python3 cli.py identity
python3 cli.py show
python3 cli.py check
```

Start with [WHAT_IS](docs/WHAT_IS.md) for the conceptual map, then [RESEARCH_MAP](docs/RESEARCH_MAP.md) for source-to-claim relationships and current limits. [HOW_TO](docs/HOW_TO.md) gives a reproducible reading and evidence procedure.

[Hardware-adaptive placement](docs/HARDWARE_ADAPTIVE_PLACEMENT.md) observes storage and memory, checks an AI-selected batch, uses the existing owner transfer CLI, and verifies that USL resource IDs, meanings, roles and provenance survive location changes. Run `python3 scripts/placement_graph.py check` and `python3 scripts/placement.py --help`. Private host registrations stay under ignored `.local/`; the CLI preserves source files.

The [hardware and software fit plan](docs/HARDWARE_SOFTWARE_FIT_PLAN.md) extends that direction toward hardware-specific native program variants, execution settings and data placement under CHU OS. The [verbatim user statement](records/2026-10-10/hardware-software-fit/user-verbatim.txt) is separate from the [proposed graph and runtime contracts](graph/hardware-software-fit.proposal.json). This is a HOW_TO design, with phased acceptance criteria; it does not claim a deployed autonomous runtime. Validate the design with `python3 records/2026-10-10/hardware-software-fit/validate.py`.

The [2026-10-10 OMC and MHC purpose note](docs/RESOURCE_CREDIT_AND_SHARED_INTELLIGENCE.md)
records the user's direction: continuously contribute computing resources, earn credits,
and use the larger HSWM·CHU intelligence through a P2P economy and mutual agreement.
The [verbatim request](records/2026-10-10/resource-credit-shared-intelligence/user-verbatim.txt)
is preserved separately from the explanatory design note and the older source archive.

## Content index

Start with [philosophical and technical-philosophical OMC](docs/OMC_LOGICAL_FOUNDATIONS.md)
for the argument connecting existence, persistence, shared intelligence and the
meaning, learning, resource and agreement loops. The [source review](docs/OMC_FOUNDATION_SOURCE_REVIEW.md)
separates inherited statements from the new reasoning; the [argument graph](graph/omc-foundations.json)
keeps inferential dependencies separate from conditional feedback cycles.

The [OMC perspectives and MIND sources](docs/OMC_PERSPECTIVES_AND_MIND.md) preserve
the user's distinction between technical OMC, actual philosophical OMC, and OMC
as seen by Dimension Walker. Five complete MIND texts, including the airplane-man
CLOUD CONNECT scene, are preserved with their provenance in the
[2026-10-10 source record](records/2026-10-10/mind-omc-perspectives/README.md).

The [token-efficiency flywheel](docs/FLYWHEEL.md) starts with a testable premise:
the same base LLM and total token budget should yield more useful answers through HSWM·CHU.
See the [generated cycle diagram](docs/FLYWHEEL_GRAPH.md) and [typed graph](graph/flywheel.json).
Run `python3 scripts/flywheel.py check` for provenance and graph validation, or
`python3 scripts/flywheel.py query` for the premise, accounting rules and evaluation status.
Performance and economic effects remain hypotheses awaiting experiments.

`APOSTLE_CONTENT.json` lists the original SYMPOSIUM archive's files, byte digests, and source revision. That archive begins at `sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/`; it is `SOURCE_DOCUMENT`. The MIND snapshots have their own [source manifest](records/2026-10-10/mind-omc-perspectives/sources.json). This README and `docs/` are `SECONDARY_AI` guides. “OMC” is the canonical abbreviation for Orbital Motion Cloud; “OMD” is a separate shared-source-of-truth / coordination reference, not an alias for this apostle.
