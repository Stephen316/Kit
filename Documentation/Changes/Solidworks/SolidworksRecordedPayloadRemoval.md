# SOLIDWORKS recorded payload removal

## Change

The supported SOLIDWORKS families were described as constructive with zero opaque bytes.
Each family under `src/convert/adapters/solidworks/programs/` was a recorded payload.
A recorded payload is one vendor-saved stream, re-encoded as typed field operations.
Each operation stored an absolute offset, a width, an owner, a kind, and the value from that save.
The writer re-emitted the list at the saved length and overrode selected offsets.
This form could not change object count or topology, so each new profile needed another recorded program.
Every generated file, including files that SOLIDWORKS could not load, also took its `Config-0` stream from one recorded configuration program.

This change removes SOLIDWORKS writing:

- The SOLIDWORKS adapter no longer defines `supports` or `write`, so the registry lists it as a reader only.
- The 43 recorded programs, the revolve envelopes, the configuration and assembly program modules, and the writer code in `core/Adapter.py`, `core/Native.py`, and `assembly/Assembly.py` are deleted.
- `write_sldprt` is no longer exported.
- `re/tooling/ProgramDecomposition/`, which generated the programs, and `tools/audit/`, which measured FCStd to SOLIDWORKS output, are deleted.
- `tools/Donors/CheckReplays.py` fails when `src` contains any recorded field operation or recorded payload re-emission call.
  The `Python steering` workflow runs it for pull requests, merge groups, and `main`.
- [AGENTS.md](../../../AGENTS.md), the preamble of the [no donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md), the [SOLIDWORKS adapter guide](../../Reference/Adapters/Solidworks.md), the README format table, and the research notes describe the read-only state and the required generative direction.

The container, archive, configuration manager, definition, resolved-feature, and Parasolid codecs remain.
They contain no recorded field programs.

## Behavior

| Operation                                      | Result                                                     |
| ---------------------------------------------- | ---------------------------------------------------------- |
| Read a `.SLDPRT` or `.SLDASM` file             | Unchanged                                                  |
| Convert to a `.SLDPRT` or `.SLDASM` path       | `AdapterNotFoundError`: no writer supports the destination |
| Write with `destination_format="solidworks.*"` | `AdapterNotFoundError`: no writer is registered            |
| Read a SOLIDWORKS file that Kit wrote earlier  | Reads the embedded Kit document                            |

A file that Kit wrote earlier carries an attestation that only the removed generator could verify.
Its `solidworks.container_compatibility` metadata now reads `kit-neutral-only`.

A recorded field operation is a tuple literal that starts with two integer literals and has a lowercase kind string, such as `primitive:double` or `classref`, as its fourth item.
A recorded payload re-emission call is a call to `ReplayResolved`, `ReplayFixed`, `ReplayAssembly`, or `ReplayConfig`.

| Check result                                 | Exit status |
| -------------------------------------------- | ----------: |
| No recorded payload in the scanned files     |           0 |
| A file contains a recorded payload           |           1 |
| A path is missing or a file cannot be parsed |           2 |

## Usage

Run the check from the repository root:

```sh
uv run python -m tools.Donors.CheckReplays src
```

## Limits

The check detects the field-operation tuple form and the four re-emission calls.
It does not detect recorded bytes in other forms, such as encoded blobs or captured tables.
Review and the no donor blocks standard still apply to those forms.
SOLIDWORKS output returns only when a generative serializer passes the acceptance rules in the standard.

## Verification

The check reports no recorded payloads in the 3,066 Python files under `src`.
It reports a deleted program file as a recorded payload.
Black, Ruff, mypy, pyright, repository-wide steering, path policy, zizmor, and Prettier passed locally.
The tests were not run locally under the repository test policy.
The pull request checks do not run the test suite, so the merge queue is the first run of the changed tests.

## Related information

- [Zero opaque bytes is not generation](../../Gotchas/Conversion/ZeroOpaqueBytesNotGenerated.md)
- [No donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md)
- `re/solidworks/archive/Grammar.md` section 6, derived caches
