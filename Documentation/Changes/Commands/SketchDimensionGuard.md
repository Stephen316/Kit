# Qualify dimension-driven sketch conversion

Bodyless sketch conversion now requires an active driving constraint linked to
each sketch's declared parameter IDs, plus the same SDK regeneration contract
used for body geometry. Literal geometry with a reference history alone remains
inspection-only. Missing contracts and geometry that disagrees with regenerated
SDK state are refused with `UnqualifiedGeometry`. Validation requires Python 3.14.

Supported constrained rectangle sketches remain convertible. Unconstrained SDK
circle and rectangle profiles, including ones with unrelated parameters, do not
establish dimension-driven geometry. An extra inactive reference cannot qualify
them. The later [complete model guard](ParametricModelGuard.md) also checks solid
profiles and refuses parameter-only documents without model history.

Remote process coverage includes literal circle/rectangle, missing contract,
stale geometry, suppressed dimensions, and reference dimensions at root/nested
levels with absent/existing destinations. Source preservation and inspection
remain required. Existing successful native conversion coverage uses a constrained
rectangle. No local tests or decoding ran; static validation and exact-head CI
evidence are recorded in PR #119.

See [the sketch qualification gotcha](../../Gotchas/Conversion/Commands/SketchReferencesAreNotDrivingDimensions.md).
