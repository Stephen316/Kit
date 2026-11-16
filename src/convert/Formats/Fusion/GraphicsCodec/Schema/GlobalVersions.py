# the global versions vocabulary must stay centralized so graphics reconstruction agrees on supported native identities
KGlobalVersions = {
    "TextureMappingAttribute": (1,),
    "TextureEffectAttribute": (1, 2),
    "NodeData": (2,),
    "GraphicsBlobFeatures": (1,),
    "F360InstanceNode": (0, 1),
    "BillBoardAttribute": (1, 2),
    "GroupNode": (1,),
    "GraphicsGlobalVersion": (1,),
    "OGSBlobVersion": (0,),
}

# the optional versions vocabulary must stay centralized so graphics reconstruction agrees on supported native identities
KOptionalVersions = frozenset({"GraphicsBlobFeatures"})
