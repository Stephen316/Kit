# Fusion sketch labels have a separate owner

`DcSketch` inherits `DcFeature.featureUserName`, but editing that stored field did not change the controlled sketch's visible timeline name.
Treating every feature's inherited label as its public API name therefore gives the wrong observable result.

In the controlled archive, native entity 203 is `SKs::Geometry::MSketch` with `userName = Radius10mm`.
Entity 208 is `Na::DesignCapture::DcSketch`; its inherited feature fields contain no `Radius10mm` value.
After rewriting its `featureUserName`, the imported timeline still displayed `Radius10mm`.
The same field on `DcExtrudeFeature` successfully changed the extrusion's visible name.

The [failed expectation](../../../../re/Fusion/LocalOracle/Features/GraphAcceptanceNameFailure.json) and [native property capture](../../../../re/Fusion/LocalOracle/Features/extrude_07mm.entities.json) record the distinction.
The corrected acceptance case preserves the sketch's label and edits only the extrusion's `featureUserName`.
A general sketch renamer must account for the sketch geometry object's naming field rather than applying the extrusion naming rule universally.
