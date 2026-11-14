# Fusion native parameter serialization

## Behavior

The numeric reader now decodes the owning collection reference instead of requiring object identity 16.
Projected parameter attributes include `fusion.collection_id`.
Reference framing and end-of-record validation remain strict.
Existing graph-level checks still verify reciprocal collection membership.

Internal serializers construct the qualified numeric parameter, floating binding, parameter collection, and name registry payloads from typed fields.
The serializers derive lengths, counts, reference framing, repeated owner references, and known metadata profiles.
They reject unsupported metadata and invalid identities.

The `Fusion archive compatibility` CI job exercises complete saved archives on Python 3.14.
It runs on pull requests, merge groups, and main pushes.
The CI allowlist includes this job in both pull-request and merge-group health checks.

## Usage and limitations

These modules extend `convert.formats.Fusion.SegmentCodec.Parameters`.
They feed the existing segment writer, which derives updated record offsets.
They are internal native-format components, not a complete Fusion document writer.
The explicit partial reader remains the supported research entry point.

The [data model](../../Reference/Research/FusionDataModel.md) explains archive structure, parametric ownership, B-rep history, and unresolved generation requirements.
The [collection-reference gotcha](../../Gotchas/Conversion/Fusion/FusionParameterCollection.md) describes the corrected assumption.
The [archive-inspection gotcha](../../Gotchas/Conversion/Fusion/FusionArchiveInspection.md) records the REA compression boundary.

## Evidence

The local corpus inventory inspected 712 archives and 21,269 central-directory entries.
REA 6.8.0 inspected the F3Z example and recorded its eleven contained entries.
Source inspection corroborated the collection reference against the existing reciprocal membership decoder and study grammar.
General automated tests run in remote CI.
After explicit local-oracle authorization, Fusion accepted a Kit-edited parameter archive and retained a rebuilt dependent expression after save and reopen.
See the [recorded acceptance scope](../../../re/Fusion/LocalOracle/Rewritten/Acceptance.json); it does not establish complete native document generation.
The deletion and reallocation captures show that the parameter table's allocation high-water mark is independent of its member count.
The schema dump names this member `highWaterMark`.
The writer accepts that mark explicitly instead of deriving it from surviving members.
