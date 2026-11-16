# Saved Parasolid faces can list the hole first

A saved SOLIDWORKS face carries its Parasolid trimming loops in native traversal order. The eleven pinned P04 discovery files put an inner rectangular loop before the exterior on each holed cap. The two cap loops on the through-all result follow the same order.

Use the geometric role to distinguish the exterior and hole. Preserve the native traversal order for topology and provenance. The reader derives the role for closed planar line rings with strict containment. Curved or ambiguous boundaries retain the existing fallback. [Reader change](../../../Changes/Research/Readers/SolidWorks/ParasolidLoopRoles.md)
