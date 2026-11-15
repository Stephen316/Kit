# Native field write refusal

Document writers now refuse unresolved sketch geometry, constraint bindings and
extrusion terminations before changing a destination. The checks apply after
source relabeling and JSON persistence, including suppressed and nested documents.
They remain active when write validation is disabled.

The checks inspect these explicit typed fields:

- `NativeGeometry`, native geometry kinds and unknown geometry kinds.
- Native or unknown constraint kinds, empty participating-entity references,
  dangling entity references and dangling parameter bindings.
- Missing parameter bindings for `distance`, `distance_x`, `distance_y`, `angle`,
  `radius` and `diameter` constraints. These kinds have no other typed numeric
  value in `SketchRelation`. Geometric constraints can omit a parameter binding.
- Missing sketch parameter references.
- Native or unknown primary extrusion and hole end conditions, and secondary
  extrusion end conditions, including those without a secondary length.

The existing native-feature refusal retains its diagnostic. This change does not
infer semantics from attribute names, retained native values or opaque bytes.
Known enum vocabulary does not establish destination support. Each writer's
existing capability checks still apply.

Manual model JSON serialization remains available for inspection and persistence.
Retained native data must be decoded and independently qualified before export.

## Verification

`tests/convert/solidworks/core/NativeWrites` adds persisted compatibility cases
through public conversion/writing and direct writer file/stream boundaries.
The cases check destination preservation, relabeled sources, suppressed history
and nested documents. Native sketch evidence comes from the existing saved
SOLIDWORKS sample, isolated inside an independently authored Fusion document.
Other cases persist explicitly unresolved termination values and missing bindings.
An independent constrained Fusion cuboid remains the positive write/read control.

Steering, Mypy, Pyright and Black checks are required before publication. Local
tests were not run; remote execution is pending for this revision. This refusal
check does not qualify native geometry, constraints, field maps or CAD output.

See [the field-retention gotcha](../../../Gotchas/Conversion/NativeSketchFieldRefusal.md).
