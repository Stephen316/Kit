# TSM edge end conditions are not crease flags

A record such as `ec 12 0` can look like an edge index plus integer crease flags. Kit reads the second field as a binary64 end-condition scalar. That type comes from earlier binary inspection and is not confirmed by a black-box experiment.

User crease state is stored separately by namespace 100. Native interior-edge crease/uncrease leaves boundary `ec` records unchanged. Decode the scalar as a float, retain its edge identity and reject nonzero values until their additional behavior is qualified.

[Crease differentials](../../../../../re/Fusion/Reconstruction/TSpline/CreaseInventory.json) establish the distinction.
