# Validation of the planned 0.3.0 changes

Delivery target: GitHub pull request. npm publication is deferred by the maintainer;
do not create a release or retry publication until explicitly requested.

## Scope and compatibility

The implementation combines project-aware catalog and lifecycle hardening with
evidence-based selection and the public Prompt Designer skill. The approved flow
is grilling plus Prompt Designer, a persistent local specification, then Maestro
execution in the same conversation through the complete requested objective.

The JSON migration replaces `confidence` and automatic loading with retrieval
evidence and candidate review. Domain hints stay soft by design: candidates from
other domains remain eligible. This intentionally replaces main's strict explicit
domain filter, while preserving its Unicode normalization, metadata phrase boosts,
declared-domain handling (including the cybersecurity alias), and suppression of
the Portuguese phrase `com segurança` as a cybersecurity routing signal.

Tests from main are retained against the new versioned catalog. Synthetic global
fixtures use a global scope; active project skills are tested with real temporary
project directories to preserve project isolation.

## Checks

- Python behavior, project isolation, privacy and archive regression tests.
- Node CLI, both-skill installation/upgrade/removal, rollback and package parity tests.
- A curated 23-case English/Portuguese retrieval benchmark, including a greeting
  followed by a task, unknown terminology and short technical terms.
- Actual archive inventory, common credential/personal-path scan and SHA-512 checks.
- Installation of each actual archive in an isolated directory, followed by setup,
  upgrade, doctor, search, batch routing and removal.
- Independent instruction scenarios: complete offline application handoff and a
  reproduced defect whose diagnosis/implementation candidates have different scopes.

The skill-creator validator accepts Prompt Designer. Maestro retains the existing
host-specific `disable-model-invocation` field, which the generic validator does
not recognize. Its core schema was validated on a temporary copy without that
field; the original invocation policy remains unchanged.

## Limits

Passing a curated retrieval set is not measured production accuracy and does not
guarantee the agent's semantic judgment. Metadata never substitutes for reading
candidate instructions. Automated secret scanning complements manual review but
cannot establish that arbitrary business prose is public. Actual project briefs,
local manifests, machine paths and private installation files are excluded from
public artifacts.

Local validation ran on Windows with Node 22 and Python 3. The GitHub PR checks
provide Linux and Windows validation of the merged revision. No npm release is
part of this delivery.
