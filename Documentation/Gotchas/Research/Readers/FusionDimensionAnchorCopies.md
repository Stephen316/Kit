# Fusion P04 dimension records carry two point orders and divergent anchor copies

The P04 Fusion height and center dimensions store their two point references in reverse order between the dependency prefix and the operand tail. Matching the lists by position loses these records. Match the same typed point pair within one sketch and keep the tail order and dependency order separately. This branch applies to the observed horizontal and vertical linear dimensions.

Four planar size edits also retain divergent copies of some cached annotation anchors even when the scalar and live parameter agree. Keep the geometry cache unresolved when those copies disagree and report both coordinates. The saved binding and historical API measurement are separate evidence for the live parameter. [P04 sketch evidence](../../../Changes/Research/Readers/FusionCutSketchEvidence.md)
