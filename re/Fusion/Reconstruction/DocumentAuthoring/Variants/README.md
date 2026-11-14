# Independently authored circle and extrusion research

`AuthorCircle.py` extends the explicit document constructor with a positive-Z
XY circle. `build_circle(specification)` returns `metadata`, `bulk`, and `model`
in the same shape as the empty-document builder. It does not load a source
archive, captured object graph, or original payload. The current generated
candidate has radius 12.5 mm, one sketch feature, one unrelated free user
parameter, 112 entities, 135 physical records, and 132 class declarations.
Native acceptance is pending.

`CircleSpecification.json` adds these semantic inputs to the empty specification:

- `assetId`, which must be the exact UUID of the independently authored asset
- `sketchName` and `radiusMillimeters`
- `sketchGeneration`, an explicit named-metadata generation marker
- `firstSketchTag`, the first newly allocated sketch tag
- `firstOperationId`, the first newly allocated feature operation ID

The new circle has a separate origin point and center point, a `CircArc3D`
defined analytically from its center, positive-Z normal, positive-X reference
vector, radius, and full `0..2π` interval. Its center-point curve-use table
points back to the circle. The sketch owns its geometry, has an identity
coordinate system, and joins the `SketchesRoot` root and component sketch
collection. New primary/secondary tags are allocated semantically, not taken
from object IDs or a payload. The collection tag counter advances accordingly.

The `DcSketch` owns an input reference to the authored XY origin plane and a
`DRMatrix` linked to that reference. The component reference scope uses the new
component persistent UUID and the supplied asset UUID. The plane recipe uses
the newly allocated origin-plane object identity. Analytic plane and matrix
caches are generated from those same geometric definitions. All dynamic cache
validity flags are false and the dependency/compute maps start empty; native
reconstruction of those maps remains an acceptance requirement.

The creation-order list contains the authored sketch feature. The feature ID
manager maps the chosen first operation to that new node, and the component
operation seed advances by one. The candidate writes feature-language
generation 260 and sketch constraint generation 7, and Fusion accepted the
circle candidate with these values. Earlier binary inspection
tied these to the installed build; that evidence was removed and is not
confirmed by a black-box experiment. The generation marker in named
metadata and the interpretation of some data-reference flags remain qualified
policy choices pending native acceptance, not universally proven defaults.

`GeneratedCircle/Generation.json` binds the exact candidate streams and expanded
semantic model. The raw model is ignored; the complete generated model is
archived in `GeneratedCircle/AuthoredModel.json.xz`. Regeneration intentionally
creates new persistent identities and therefore changes the bulk digest. The
empty candidate in the parent directory remains unchanged.

## Canonical profile recipe evidence

`RecipeConstructors.json` lists the canonical recipe values. The unsplit
`sketch_tag_id` recipe has version 3, the supplied primary tag, zero secondary
tag, the supplied direction, split sequence/total both 1, and the unnamed
uint64 field `objectOffset20` zero. The `profile_edge_tag_data` recipe has
version 0 and both unnamed sets empty. Earlier binary inspection of
constructors suggested these values; that evidence was removed. They are
authored policy, accepted by Fusion in the extrusion candidate.
`RecipeFields.py` exposes only this state. It cannot accept arbitrary
unidentified scalar/set contents.

This provides a source-independent route to a canonical unsplit-circle recipe.
It does not recover the nonzero meaning of the remaining scalar or nonempty
sets. Those are still explicit generic-format gaps. Earlier binary inspection
named the region face recipe's pair boolean `isOuterLoop`; that name is not
confirmed by a black-box experiment. A single positive-Z full circle has
one declared outer loop; arbitrary nested/split loop selection is outside this
candidate.

## Fresh extrusion candidate

`AuthorExtrude.py` provides `build_extrude(specification)`. It extends the
authored circle with a distance extrusion, a region/model data-reference pair,
the canonical outer-circle recipe, two numeric parameters and reciprocal
floating bindings, an extrude tool node, a result-body node, and an explicitly
declared BRep body. The current candidate has 139 logical entities, 172 physical
records, and 152 class declarations. Its radius is 12.5 mm and its height is
17.25 mm. Native acceptance is pending.

The single user parameter drives the `AlongDistance` expression. The new model
parameters have creation indices 2 and 3; the parameter-table high-water mark
is 3. The two `DcDoubleParameter` bindings use runtime parameter IDs 1 and 2,
and the fragment's next runtime parameter counter is 2. Their subscription
slots on the extrusion are explicitly 0 and 1. Each parameter is present in
the name registry, collection membership, and helper observer list.

The profile scope selects the newly authored sketch by its fresh numeric
identity. The component/plane scope selects the newly generated persistent
component UUID. All asset scope values come from the supplied `assetId`. The
region recipe is constructed from the allocated circle tag and the canonical
unsplit-tag recipe fields. A separate sketch-curve recipe uses the same
tag with reverse direction for the extrusion's profile-edge provenance.

The feature-ID maps allocate the sketch's operation and two extrusion
operations; the component allocation seed advances by three. The representation
list contains sketch then extrusion. The sketch is hidden after the extrusion.
The extrusion's start/end history-state IDs are explicit inputs, rather than
values inferred from arbitrary object IDs. Current qualified inputs reserve
the face labels `1` and `2` for the caps, use label `3` for the side-face profile
progenitor, and use progenitor tag `4` for the body. These are declared topology
names for this candidate, not a universal multi-feature naming algorithm.

The returned `model.brepContract` supplies the companion geometry writer with:

- newly generated BRep part name and body UUID
- fresh Design body identity and serializer body key
- radius, height, positive-Z placement, and operation identity
- explicit current/initial history IDs, history generation, allocation, board
  number, and the separate `generationRef` scalar
- side/top/bottom face labels, top/bottom edge labels, and primary sketch tag

The body UUID does not occur in the companion SMBH body header. The Design
serializer's map joins the chosen body key to the fresh body entity. The
independent SMBH writer must use the same operation and sketch naming values.
The new part is not written by this module; container orchestration adds the
generated geometry at the declared BRep part path. No source blob is an input.

The body mass cache contains analytic geometric moments about the world origin,
using centimeters: volume `πr²h`, area `2πr(r+h)`, center `(0,0,h/2)`, transverse
moments `volume·(r²/4+h²/3)`, and axial moment `volume·r²/2`. Off-diagonal moments
are zero by symmetry. The cache revision is the zero UUID so it does not assert
correspondence with an unknown kernel revision. The native application must
calculate its authoritative cache from the authored geometry.

Important additional qualifications:

- Profile/tool topology caches are absent and dynamic cache-valid flags are
  false; the semantic feature and recipe graph must regenerate them
- Dependency maps are empty and explicitly marked noncurrent
- The body passive-identity generator starts empty; no captured scan order is
  imported, and native acceptance must establish the required initialization
- The physical material is the empty value; visual material uses
  an explicitly selected gray custom color with no material package
- `generationRef` remains an explicit scalar whose general identity semantics
  are not yet established; the qualified candidate supplies the independently
  accepted history profile's value without treating it as a general default
- Nonzero unnamed sketch-tag slots and nonempty unnamed profile-edge sets
  remain unsupported by the canonical authoring interface

These qualifications prevent the research candidate from being described as a
complete arbitrary-document writer before the receiving application accepts
initial geometry, rebuild, parameter editing, save, and reopen.

## Native loading invariant

Fusion rejected an ACT stream whose primary bulk offsets did not increase with
entity identity, and accepted it after only the physical order changed.
Continuations may stay inside their owner's span; globally moving all
continuations to the end was not needed. The Design builders allocate and emit
ascending primary IDs. Earlier binary inspection described the general rule;
beyond these cases it is not confirmed by a black-box experiment.
