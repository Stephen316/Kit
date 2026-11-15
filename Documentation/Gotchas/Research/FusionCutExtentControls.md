# Fusion cut direction and object IDs across extent variants

The P04 Fusion blind baseline stores a positive direction vector with a negative distance. The negative through-all variant stores a negative direction vector and has no along-distance binding. Interpreting direction requires the saved end code and its active operands.

The through-all archive also uses the same object ID `461` for an end reference that the blind baseline uses for the distance parameter object. Resolve IDs within each archive’s indexed class and object tables before assigning a role. The through-all reference and associated flags remain unresolved. [P04 archive evidence](../../Changes/Research/Readers/FusionCutExtentEvidence.md)
