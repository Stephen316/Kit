# the face corners order must stay explicit so geometric values retain their native record boundaries
KFaceCorners = (
    (0, 2, 3, 1),
    (4, 5, 7, 6),
    (0, 1, 5, 4),
    (2, 6, 7, 3),
    (0, 4, 6, 2),
    (1, 3, 7, 5),
)

# edge corners must remain consistent across callers so geometric values retain their native record boundaries
KEdgeCorners = tuple(
    (Corner, Corner | AxisFlag)
    for AxisFlag in (1, 2, 4)
    for Corner in range(8)
    if not Corner & AxisFlag
)

# first face must remain consistent across callers so geometric values retain their native record boundaries
KFirstFace = 4

# first loop must remain consistent across callers so geometric values retain their native record boundaries
KFirstLoop = KFirstFace + len(KFaceCorners)

# first coedge must remain consistent across callers so geometric values retain their native record boundaries
KFirstCoedge = KFirstLoop + len(KFaceCorners)

# first edge must remain consistent across callers so geometric values retain their native record boundaries
KFirstEdge = KFirstCoedge + 4 * len(KFaceCorners)

# first plane must remain consistent across callers so geometric values retain their native record boundaries
KFirstPlane = KFirstEdge + len(KEdgeCorners)

# first vertex must remain consistent across callers so geometric values retain their native record boundaries
KFirstVertex = KFirstPlane + len(KFaceCorners)

# first curve must remain consistent across callers so geometric values retain their native record boundaries
KFirstCurve = KFirstVertex + 8

# first point must remain consistent across callers so geometric values retain their native record boundaries
KFirstPoint = KFirstCurve + len(KEdgeCorners)
