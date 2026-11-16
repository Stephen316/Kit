# Saved Parasolid faces can list the hole first

A saved SOLIDWORKS face carries its Parasolid trimming loops in native traversal order. The eleven pinned P04 discovery files put an inner rectangular loop before the exterior on all twelve holed caps, including both through-all caps. At `14f4a1f2`, the decoder also labelled the first ring as outer on all four caps in the two automatic-scope saves. Each opening was 80 mm². The enclosing perimeters were 800 mm² for body A and 200 mm² for body B. [Automatic-scope partition evidence](../../../Changes/Research/Workers/SolidWorks/AutomaticScopePartitionGeometry.md)

Use the geometric role to distinguish the exterior and hole. Preserve the native traversal order for topology and provenance. The reader derives the role for closed planar line rings with strict containment. Curved or ambiguous boundaries retain the existing fallback. [Reader change](../../../Changes/Research/Readers/SolidWorks/ParasolidLoopRoles.md)
