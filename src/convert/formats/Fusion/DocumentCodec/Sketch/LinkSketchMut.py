from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole


def LinkSketchMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    SketchName = SketchRole(Author)
    Author.Change(
        SketchName,
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles[SketchName]),
        rDcNode=Reference("dc_sketch"),
        UCS=Reference("sketch_coordinates"),
        rSketchGroupParent=Reference("sketches"),
        userName=Author.SpecValue.SketchName,
    )
    Author.Change(
        "sketches_root", rootId="SketchesRoot", rooted=[Reference(SketchName)]
    )
    Author.Change("sketch_origin", curveUses=Reference("origin_uses"))
    Author.Change(
        "dc_sketch",
        rSketch=Reference(SketchName),
        rSketchPlaneMatrix=Reference("sketch_matrix"),
        childNodes=[Reference("sketch_plane"), Reference("sketch_matrix")],
        featureBaseName="Sketch",
        rProgenitorTable=Reference("sketch_progenitors"),
    )
    ScopeValue = [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=Author.ComponentId,
                scopeIdType=2,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
    Author.Change(
        "sketch_plane",
        rRecipe=Reference("plane_recipe"),
        rScope=ScopeValue,
        caches=[Reference("plane_cache")],
        trackingType=33,
        updateFlag=4,
        rParentFeature=Reference("dc_sketch"),
    )
    Author.Change("plane_recipe", m_entityId=Author.Roles["xy_plane"])
    Author.Change(
        "sketch_matrix",
        dataRefs=[Reference("sketch_plane")],
        caches=[Reference("matrix_cache")],
        trackingType=4,
        rParentFeature=Reference("dc_sketch"),
    )
    PlaneValue = dict(
        normalReversed=False,
        origin=MakePoint(),
        uAxis=MakePoint(1.0),
        vAxis=MakePoint(0.0, 1.0),
    )
    Author.Change(
        "plane_cache",
        rCachedGeometry=PlaneValue,
        progenitor=Reference("plane_progenitor"),
    )
    Author.Change(
        "plane_progenitor", m_entityRecipe=Reference("plane_progenitor_recipe")
    )
    Author.Change("plane_progenitor_recipe", m_entityId=Author.Roles["xy_plane"])
    for RoleName in ("dc_sketch", "sketch_plane", "sketch_matrix"):
        Author.Change(
            RoleName,
            status=Reference(RoleName + "_status"),
            rDynamicUpdateData=Reference(RoleName + "_dynamic"),
        )
        Author.Change(
            RoleName + "_dynamic",
            rOwnerNode=Reference(RoleName),
            timeStamp=Author.Policy.TimeStamp,
        )
    Author.Change("sketches", highWaterMark=1, groupChildren=[Reference(SketchName)])
    Author.FindEntity("sketches").NamedPairs = MakeAttributes(
        crv_tag_id_idx=Author.Policy.FirstSketchTag
        + (9 if Author.SpecValue.ProfileKind in ("rectangle", "cuboid") else 3)
    )
    Author.Change("fragment", featureIndexMap=[{"key": "DcSketchMetaType", "value": 1}])
    Author.Change("creation_order", representationFeatures=[Reference("dc_sketch")])
    Author.Change(
        "feature_ids",
        featureIdMap=[
            {"key": Author.Policy.FirstOperationId, "value": Author.Roles["dc_sketch"]}
        ],
    )
    Author.Change("component", operationSeedId=Author.Policy.FirstOperationId + 1)
