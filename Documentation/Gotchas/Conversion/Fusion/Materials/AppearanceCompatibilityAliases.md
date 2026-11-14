# Native appearance references can resolve to a compatibility partner

A body's appearance `assetReference` need not identify the instance whose definition and library IDs appear in that same body value. A native saved package can store a legacy `Generic` appearance at the base identity and the current appearance at the exact base identity plus `_Post2015`.

Earlier binary inspection suggested a resolution rule. If both instances exist, Fusion selects the suffixed instance. If the base instance is missing, the suffixed instance alone does not resolve. No black-box experiment confirms this rule.

Kit applies this resolver before checking the selected asset's role, definition and library. Preserve both persisted instances when regenerating the package. Do not bypass those checks or search for any asset with a matching definition. [Native document links](../../../../../re/Fusion/Reconstruction/OgsScene/NativeMaterialLinks.json) show the paired identities in both controls.
