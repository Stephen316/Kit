# SOLIDWORKS planar cap holes can precede the exterior loop

The first dimensioned loop in the saved traversal can be the hole. At `14f4a1f2`, the Parasolid decoder used that order to label the first non-isolated ring as outer. In the two automatic-scope saves this labelled the 80 mm² opening as outer on all four caps. The attached box perimeter was 800 mm² for A and 200 mm² for B. The same inversion appeared on 12 holed cap faces across all eleven P04 discovery variants, including the YZ support and the through-all cut.

Preserve native loop order as structural evidence. Establish the planar boundary role from the face geometry. The [scope partition replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopePartitionGeometry.md) checks both nested rectangular rings against the typed cap and recipe coordinates. Its mass integration uses the oriented coedges.
