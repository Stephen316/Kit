KFaceCorners = (
    (0, 2, 3, 1),
    (4, 5, 7, 6),
    (0, 1, 5, 4),
    (2, 6, 7, 3),
    (0, 4, 6, 2),
    (1, 3, 7, 5),
)
KEdgeCorners = tuple(
    (Corner, Corner | AxisFlag)
    for AxisFlag in (1, 2, 4)
    for Corner in range(8)
    if not Corner & AxisFlag
)
KFirstFace = 4
KFirstLoop = KFirstFace + len(KFaceCorners)
KFirstCoedge = KFirstLoop + len(KFaceCorners)
KFirstEdge = KFirstCoedge + 4 * len(KFaceCorners)
KFirstPlane = KFirstEdge + len(KEdgeCorners)
KFirstVertex = KFirstPlane + len(KFaceCorners)
KFirstCurve = KFirstVertex + 8
KFirstPoint = KFirstCurve + len(KEdgeCorners)
