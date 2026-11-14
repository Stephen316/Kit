# ParaMesh corner domains and terminal words

A shared stream descriptor does not imply a shared delta encoding. The triangle stream stores signed differences followed by a distinct terminal word. Its initial vertex is reconstructed from the full vertex-index range; the terminal word must be retained independently. Normal override, feature-edge and face-group streams instead end with the absolute final uint32 value, from which the first value is reconstructed backwards.

Normal override indices address triangle-corner positions, not vertex indices. The normal table first supplies one entry per vertex and then one entry per override. Sorting or deduplicating the triangle corner sequence loses information. Replacing overrides with vertex indices or treating the triangle terminal word as an ordinary final index also loses information. The loss happens even if a mesh remains visually plausible.

Likewise, registry field 9 is not the number of face-group mappings. Every one of the 103 inspected components stores 1 there, including components with several independent group keys and UUIDs. The qualified codec keeps this field distinct and checks every triangle membership against the actual mapping.

The [field report](../../../../../re/Fusion/Reconstruction/ParaMesh/ContainerFields.json) and [wire model](../../../../../re/Fusion/Reconstruction/ParaMesh/WireModel.md) bind these observations to corpus components. The writer must preserve the original terminal word, corner ordering, override ordinal domain and separate identity mappings rather than infer convenient substitutes.
