from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole


def LinkExtrudeMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "dc_extrude",
        rAlongDistance=Reference("along_binding"),
        rTaperAngle=Reference("taper_binding"),
        rExtrudeToolBody=Reference("extrude_tool"),
        profileDataRefs=[Reference("profile_model")],
        dcBodies=[Reference("dc_body")],
        childNodes=[
            Reference(RoleName)
            for RoleName in (
                "profile_model",
                "profile_region",
                "along_binding",
                "taper_binding",
                "extrude_tool",
            )
        ],
        featureBaseName="Extrude",
        featureUserName=Author.SpecValue.ExtrusionName,
        rProgenitorTable=Reference("extrude_progenitors"),
        startModelHS=Author.Policy.HistoryInitialId,
        endModelHS=Author.Policy.HistoryCurrentId,
    )
    Author.Change(
        "extrude_tool",
        rExtrudeFeature=Reference("dc_extrude"),
        rParentFeature=Reference("dc_extrude"),
    )
    for RoleName in ("dc_extrude", "profile_model", "profile_region", "extrude_tool"):
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
    Author.Change(
        "fragment",
        dcBodies=[Reference("dc_body")],
        featureIndexMap=[
            {"key": "DcExtrudeFeatureMetaType", "value": 1},
            {"key": "DcSketchMetaType", "value": 1},
        ],
        nextParamId=2,
    )
    Author.Change(
        "creation_order",
        representationFeatures=[Reference("dc_sketch"), Reference("dc_extrude")],
    )
    OperationId = Author.Policy.FirstOperationId
    Author.Change(
        "feature_ids",
        enetityIdMap=[
            {"key": Author.Roles["dc_sketch"], "value": [OperationId]},
            {
                "key": Author.Roles["dc_extrude"],
                "value": [OperationId + 1, OperationId + 2],
            },
        ],
        featureIdMap=[
            {"key": OperationId, "value": Author.Roles["dc_sketch"]},
            {"key": OperationId + 1, "value": Author.Roles["dc_extrude"]},
            {"key": OperationId + 2, "value": Author.Roles["dc_extrude"]},
        ],
    )
    Author.Change("component", operationSeedId=OperationId + 3)
    Author.Change(SketchRole(Author), isVisible=False)
    Author.Change("dc_sketch", isVisibleBeforeRollback=False)
