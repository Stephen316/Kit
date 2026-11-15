# Embedded face reference points differ from sketch origins

The embedded support plane and its selected face geometry each contain a point. Baseline A stores the embedded reference point at `(-0.002, 0.021, 0.01)` metres and the face frame origin at `(0, 0, 0.01)` metres. Both lie on the selected cap. Treating them as the same origin shifts the sketch along the cap.

Use the face geometry root with its saved transform. The omitted basis in baseline A is identity. The YZ capture stores an explicit basis and uses the face root `(0.01, 0, 0)` metres. [Packaged P04 face support decoder](../../Changes/Research/Readers/SolidWorksFaceSupportDecoder.md)
