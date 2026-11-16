# FreeCAD two-length extrusion bindings

The native FreeCAD emitter now uses explicit ordered `length_parameter_ids` to connect forward and reverse extrusion ends to their own live spreadsheet parameters.
`LengthFwd` and `LengthRev` each receive their existing `ParamExpression` dependency.
Equal scalar values and a reordered generic parameter roster cannot exchange end ownership.

Every explicit driver must occur in the feature's parameter roster, belong to that feature, have a driving length role and agree with the corresponding inline typed length after unit conversion.
The cached lengths must agree within an absolute `1e-9` mm, with no relative tolerance.
The shared length conversion factors normalize native distance properties to millimetres while spreadsheet cells retain the parameter's declared units.
Invalid, repeated, missing, unrelated or stale end owners refuse before output is published.
Two-ended features with a parameter roster require explicit end ownership instead of value-based inference.
Literal two-ended features without a parameter roster retain literal editable properties.
The single-ended and symmetric fallback paths remain unchanged; a symmetric feature has one total-thickness driver.

The property interpretation follows the target version's [official FreeCAD 1.0.2 extrusion source](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L121-L130): forward and reverse lengths act along opposite directions; symmetric mode uses the forward length as the total and ignores reverse length.
Both native length properties participate in recomputation.
The change adds no CAD runtime, donor data, schema field or fallback carrier.
Existing linked-distance, linked-plane, open-profile and unsupported-grammar refusal gates remain in force.
The existing body-revolution and scale seed emitters pass their single forward expression through the same list contract.

## Verification evidence

The dedicated process coverage reuses the independently authored 37 × 21 mm rectangle controls from the [historical readiness preflight](../Research/Readers/Comparison/FreeCadTwoLengthReadiness.md).
It invokes the actual public `WriteDocument` route and inspects the emitted FCStd `Document.xml`, sketch link, spreadsheet aliases and both expression dependencies.
The controls cover 11/5 mm, equal 7/7 mm, each parameter roster order, and a symmetric 16 mm total.
Additional process cases cover equivalent inch/millimetre bindings and malformed, duplicate, unknown, unowned, non-driving or stale end owners.
The independent open-profile control still requires refusal with zero output bytes.

Static syntax, formatting and whitespace checks were performed.
No local tests, collection, readiness commands or CAD application runs were executed.
Hosted process execution, independent FreeCAD edits, rebuild, save and fresh reopen remain required.
This implementation repairs dependency emission; it does not establish native acceptance or relax global qualification.
The historical readiness note remains the observation of its original source checkpoint.
