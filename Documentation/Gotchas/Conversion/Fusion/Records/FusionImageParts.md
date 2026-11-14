# Image serializers name PNG parts

## Expectation

The `Images.BlobParts` folder of a Fusion document is empty.

## Actual behavior

One member of `re/Fusion/examples/.f3z/example1.f3z` holds two files `Images.BlobParts/Image.<uuid>.png`. Both are PNG files. `ImageCensus.py` finds image parts in no other corpus document. The reader sent them to the BRep reader, which raised `Unsupported Fusion document part`.

Each image part is named by the `partName` of one `ImageSerializer` record in the Design segment. Other members hold `ImageSerializer` records with an empty `partName` and no image part.

## Workaround

Read each part named `Images.BlobParts/Image.<uuid>.png` as a PNG payload into `DocumentModel.Images`. Any other member of the folder stays an unsupported document part. Check that every nonempty `ImageSerializer.partName` names one image part, and that every image part is named. Write the parts back unchanged.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#image-parts)
- [Image census](../../../../../re/Fusion/Reconstruction/ReadGaps/ImageCensus.py)
- [Image references](../../../../../re/Fusion/Reconstruction/ReadGaps/ImageRefs.py)
