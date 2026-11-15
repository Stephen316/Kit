# Fusion cut direction and object IDs across extent variants

The P04 Fusion blind baseline stores a positive direction vector with a negative distance. The negative through-all variant stores a negative direction vector and has no along-distance binding. Interpreting direction requires the saved end code and its active operands.

P03 independently varies both fields in its blind boss controls. The negative-direction variant retains the baseline `+Z` vector while its attached distance becomes `−1 cm` and its measured world bounds move to Z `[−10,0]` mm. The YZ variant changes the vector to `+X` and retains the positive distance. [P03 saved blind-boss evidence](../../Changes/Research/Readers/FusionBossDirectionEvidence.md)

The through-all archive also uses the same object ID `461` for an end reference that the blind baseline uses for the distance parameter object. Resolve IDs within each archive’s indexed class and object tables before assigning a role. The through-all reference follows a body selection route. Its flags and behavioral role remain unresolved. [P04 saved selection routes](../../Changes/Research/Readers/FusionCutSelectionEvidence.md)
