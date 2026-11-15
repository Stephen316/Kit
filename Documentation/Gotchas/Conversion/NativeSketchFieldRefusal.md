# Native fields can survive inside typed sketches

## Expectation

A document without `NativeFeature` definitions contains enough typed information
to write its sketches and extrusion history.

## Actual behavior

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576707695)
identified unresolved semantics below that feature boundary. Sketch entities can
contain `NativeGeometry` while retaining a known kind string. Sketch relations can
retain a known constraint kind with empty entity bindings. Extrusion and hole
definitions can retain `native:<code>` end conditions. JSON persistence and source
relabeling preserve these values.

Structural reference validation iterates the references that exist. An empty
constraint reference tuple therefore does not produce a missing-entity error.
Retained `native_value` attributes do not supply the typed parameter binding
needed to preserve an editable dimension.

## Workaround

Apply the explicit required-field checks before destination mutation, regardless
of optional write validation. Preserve unresolved data through manual model
serialization for inspection. Do not replace native terms, infer missing binding
identities or discard suppressed records to obtain a write result.

The [change entry](../../Changes/Research/Readers/NativeFieldWriteRefusal.md)
records the guarded fields and compatibility coverage. Remote execution remains
pending for this revision.
