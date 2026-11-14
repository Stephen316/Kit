# Independent Design segment authoring

## Status and boundary

`AuthorDesign.py` constructs an explicit empty parametric document with one user
parameter. It emits a fresh `MetaStream.dat` and `BulkStream.dat` without opening
an F3D archive, a decoded object graph, an original payload, or a blob template.
The candidate has 89 logical entities, 107 physical records, and 102 declared
classes. It is a native-acceptance candidate, not an established minimum graph
or a production-ready writer. The authoring attempt deliberately reduces
optional document state; those reductions remain unproven until the receiving
application accepts and edits the result.

This directory is research. Its runtime dependencies are the existing research
schema codec, `Reflection/Versions.json`, and `BinaryClasses.json`. Those files
supply format vocabulary: class identities, inheritance, versions, named member
types, and persistence masks. They do not supply an object instance, object
identity, default instance value, or source payload. The generic codec currently
uses the system `c++filt` utility to decode C++ type spellings. There is no CAD
runtime, process bridge, installed Fusion library, or native API in the authoring
path.

## Generation API

Call `build_document(specification)` in `AuthorDesign.py`. The result contains
`metadata`, `bulk`, and `model`. `model` records all fresh role allocations,
class declarations, field values, entity frames, and revision identities. The
input vocabulary is demonstrated by `Specification.json`:

- title, parameter name, parameter comment, and length in millimeters
- fresh Design identity start, Design segment ID, and ACT segment ID
- explicit external ACT role identities for component, instance collection,
  and root instance
- expression-language generation, cache timestamp, and extension schema versions

The expression value is constructed in Fusion's centimeter modeling units:
17.25 mm becomes 1.725. The expression string is independently formatted from
the same input length. The single parameter receives creation index 1 and its
collection high-water mark is 1. The name registry and observer-subject list
reference the newly allocated parameter and collection. There is no runtime
parameter binding because a free user parameter has no feature owner.

Example generation command:

```sh
python3 re/Fusion/Reconstruction/DocumentAuthoring/AuthorDesign.py \
  --specification re/Fusion/Reconstruction/DocumentAuthoring/Specification.json \
  --output re/Fusion/Reconstruction/DocumentAuthoring/Generated
```

Generation creates new component, instance, and revision UUIDs each time. The
instance's `lastSavedTargetRevisionGuid` is the newly generated component
revision. Consequently the bulk digest changes on regeneration even when the
semantic input is unchanged. The captured candidate's exact output digests are
in `Generated/Generation.json`. `AuthoredModel.json.xz` archives that candidate's
full semantic model; the regenerable raw JSON remains locally available and is
excluded from Git.

## Cross-segment contract

The current candidate uses these fresh semantic roles:

| Role | Segment | Identity |
| --- | --- | --- |
| Design component | 0 | 1002 |
| Design component instance collection | 0 | 1017 |
| Design root instance | 0 | 1004 |
| ACT component | 1 | 100 |
| ACT instance collection | 1 | 101 |
| ACT root instance | 1 | 102 |

Four Design fields point across the segment boundary:
`ComponentBase.rACTComponent`, `ComponentBaseInstances.rACTInstances`,
`ComponentBaseInstance.rACTInstance`, and
`DcOccurrence.path.BaseOccurrencePath.sourceACTComponent`.
The ACT writer must establish their reciprocal roles. Design itself does not
contain an asset snapshot ID or ACT revision entry. The independently authored
ACT and container layers supply those structures and their own relationships.

The root component is parented by the root instance. `ComponentsRoot.rooted`
contains the component, `ComponentInstancesRoot.rooted` contains the root
instance, and the frame of the root instance has root name `rootInstance`.
The root instance subscribes to the component. The component's child instance
collection is empty: the document root instance is not a child occurrence of
its own target component.

## Structural provenance

Earlier binary inspection of constructor routines guided this role layout.
That evidence was removed. The layout below is what the candidate declares.
Fusion acceptance in [Acceptance.md](Acceptance.md) is the black-box check.

The candidate creates asset settings and registers the root instance. It
creates the ACT component, assigns its Design component, and attaches the ACT
parent when appropriate. The component owns the component instance
collection, bodies, sketches, work geometries, joint origins, assembly
constraint collections, contacts, motion studies, parameters, surface groups,
selection groups, and custom grouping collections. Bodies connect to surface
groups, and geometry collections connect to their custom groups.

The Fusion component adds the parametric fragment, features, origin geometry,
relationships, subdivision surfaces, canvases, feature groups, decals,
annotations, meshes, canvas groups, deformers, and edit-in-place contexts.
Origin work geometry is one origin point, three axes, and three planes. The
design fragment supplies the compute, dependency, association, feature
identity, cross-reference, and node managers. The candidate declares those
roles explicitly and derives their reference identities from the allocator.

The feature graph contains an active `DcComponent` inside `DcNodes`, a
`DynamicUpdateData` owner link, an empty creation-order feature list, and one
root `DcOccurrence`. No sketch, extrusion, BRep body, or feature parameter is
hidden in this empty candidate. The history and cache body containers are
empty; their serializers have empty part names, so no SMBH part is required.

## Named field policy and constant provenance

`AuthorDefaults.py` is a declaration of authored policy values, not a dump of
vendor instance defaults. Every persisted field must be explicitly supplied
by the role builder or a named class policy. The builder checks the complete
field-name set against the selected schema and rejects missing or unexpected
fields. It does not fill an unknown member with zero or preserve unexplained
bytes. The following distinctions are essential:

| Field family | How values are obtained | Evidence limit |
| --- | --- | --- |
| Object and parent references | Fresh allocator plus explicit semantic roles | Accepted in this profile; reciprocal target graph still needs acceptance |
| List, map, and group contents | Deliberately empty design, or declared owned children | Empty logical state, not copied bytes |
| Component/instance UUIDs | New UUID4 values | Cross-field equality is constructed where required |
| Parameter name, expression, value, unit, comment | Semantic input and centimeter conversion | Native edit/reopen acceptance pending |
| Parameter birthday | Authored policy value 6 | Accepted in this profile; not confirmed as a vendor default |
| Operation allocation seed | Authored policy value 300 | Accepted in this profile; not confirmed as a vendor default |
| As-built position flag, component opacity, subtype | Authored policy values `true`, `1.0`, `0` | Accepted in this profile; not confirmed as vendor defaults |
| Feature allocation counter | Authored policy value 1 | Accepted in this profile; not confirmed as a vendor default |
| Four mass-property overrides | Authored policy: four doubles set to -1 | No override requested; not confirmed as a vendor default |
| Root occurrence creation state | Authored policy value 3 | Accepted in this profile; not confirmed as a vendor default |
| Root occurrence selected state | Authored policy value -1 | Accepted in this profile; not confirmed as a vendor default |
| Empty physical material | Authored policy: four persisted strings empty, manager reference null | Accepted in this profile; general sufficiency unproven |
| Visibility/selectability and empty collection counters | Explicit authored empty-document policy | Valid field vocabulary; not claimed to prove all vendor constructor defaults |
| View position, extents, colors, annotation settings, axis/plane display extents | Explicit presentation choices | Chosen values, intentionally independent of captured user preferences |
| Unit choices and simple-unit enum values | Declared unit vocabulary, corroborated by the controlled native unit system | One complete mm/MKS system is authored; omission of other systems is unproven |
| Dynamic-update timestamp | Explicit input, initially zero with cache-valid flags false | Not represented as a current native timestamp; native rebuild behavior pending |
| Extension versions | Explicit named dictionary: Application 9, Server 7, VolField 7 | Values corroborated by the current native format; not opaque tail words |

Earlier binary inspection suggested several of these values. That evidence was
removed. The values above are confirmed only by Fusion accepting the authored
documents in [Acceptance.md](Acceptance.md). Generic containers, value
callbacks, references, root frames, and named metadata are documented in
`../EntityGraph/DataModel.md`. The Color encoder uses the custom RGBA order
documented there, not reflected lexical member order.

## Metadata emitted from semantics

The class table is a closure of the authored objects, inherited groups,
registered member value types, and nested value groups. The writer assigns
fresh class codes from 256. It emits current declared schema versions and
addin names from the schema vocabulary. It derives class ownership lists from
the primary records, root identities from root frames, bulk offsets from newly
encoded record lengths, and `nextId` from the role allocator.

The Design header uses stream version 8, marker 1234, neutron type 1, zero
initial segment current-version UUID, and an empty ancestry vector. The saved
software word is computed as `(2706 << 50) | (1 << 38) | 17`. These are typed
format values; the writer does not copy an old metadata header. The packed
software/current-version/ancestry interpretation is documented by the separate
container research. Fusion-owned classes in this qualified profile emit their
external base as a continuation; all other qualified inherited groups remain
in the primary record. This is the demonstrated profile partition, not a
universal rule for arbitrary future addins.

## Deliberate reductions requiring native evidence

The candidate has an empty Protein asset manager and empty physical-material
value, with no `.protein` package. It has no render-setting object, no default
camera/named-view objects, no VisualAnalyses root, no configuration serializer
triggers, and no Browser segment generated by this writer. The unit root
contains only one complete mm/MKS system. None of these reductions is claimed
to be universally supported. They isolate the smallest remaining native
questions without introducing a donor graph or a blob placeholder.

The next acceptance must open the independently constructed envelope, verify
the parameter and empty timeline/body state, edit the parameter, create a
sketch/feature through the application's native API, rebuild, save, and reopen.
If a root is required, add its semantic model and black-box evidence; do not
copy its captured payload. Subsequent circle/extrusion authoring belongs in
`Variants/` and must leave this captured empty candidate unchanged while that
acceptance is pending.
