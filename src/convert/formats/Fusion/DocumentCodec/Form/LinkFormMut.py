from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState

KCachedEntity = 0


def LinkToolMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "form_tool",
        rTSplineFeature=Reference("form_feature"),
        toolbodyCaches=[Reference("form_tool_cache")],
        rParentFeature=Reference("form_feature"),
    )
    Author.Change(
        "passive_ids",
        nextId=KCachedEntity + 1,
        scanOrderIndex=[KCachedEntity],
        addressOfTopEntities=[0],
    )
    Author.Change(
        "form_tool_cache",
        cachedEntityId=KCachedEntity,
        scope=[
            Author.MakeGroup(
                "PassiveScopeValue",
                dict(
                    assetId=Author.AssetId,
                    scopeEntityIdentifier=Author.ComponentId,
                    scopeIdType=2,
                    segmentId=Author.Policy.DesignSegmentId,
                ),
            )
        ],
        progenitor=Reference("form_tool_progenitor"),
    )
    Author.Change("form_tool_progenitor", m_entityRecipe=Reference("form_tool_recipe"))
    Author.Change("form_tool_recipe", m_entityId=Author.Roles["form_node"])
    Author.Change(
        "form_data",
        rBaseFeature=Reference("form_feature"),
        rParentFeature=Reference("form_feature"),
    )


def LinkGraphMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    FeatureRef, DataRef, ToolRef = (
        Reference("form_feature"),
        Reference("form_data"),
        Reference("form_tool"),
    )
    ComponentRef = Reference("dc_component")
    Author.Change(
        "compute",
        sortIsCurrent=True,
        sortedNodesAll=[ComponentRef, ToolRef, FeatureRef, DataRef],
    )
    Author.Change(
        "dependency",
        mapsAreCurrent=True,
        predecessorMap=[
            {
                "key": FeatureRef,
                "value": [
                    {"key": ComponentRef, "value": 4096},
                    {"key": ToolRef, "value": 1},
                ],
            },
            {"key": DataRef, "value": [{"key": FeatureRef, "value": 1}]},
        ],
        successorMap=[
            {"key": ComponentRef, "value": [{"key": FeatureRef, "value": 4096}]},
            {"key": FeatureRef, "value": [{"key": DataRef, "value": 1}]},
            {"key": ToolRef, "value": [{"key": FeatureRef, "value": 1}]},
        ],
    )


def LinkFormMut(Author: AuthorState, SpecValue: FormSpec) -> None:
    Reference = Author.Reference
    Operation = Author.Policy.FirstOperationId
    Author.Change(
        "form_feature",
        rTSplineToolBody=Reference("form_tool"),
        subDInfoMap=[
            {
                "key": Reference("form_node"),
                "value": {
                    "first": Operation + 1,
                    "second": Reference("form_node_tags"),
                },
            }
        ],
        rDirectModelingData=Reference("form_data"),
        dcBodies=[Reference("dc_body")],
        childNodes=[Reference("form_data"), Reference("form_tool")],
        featureBaseName="Form",
        featureUserName=SpecValue.FeatureName,
        rProgenitorTable=Reference("form_feature_tags"),
        startModelHS=Author.Policy.HistoryInitialId,
        endModelHS=Author.Policy.HistoryCurrentId,
        status=Reference("form_feature_status"),
    )
    Author.Change("form_tool", status=Reference("form_tool_status"))
    LinkToolMut(Author)
    Author.Change(
        "fragment",
        dcBodies=[Reference("dc_body")],
        featureIndexMap=[{"key": "DcTSplineFeatureMetaType", "value": 1}],
        nextParamId=0,
    )
    Author.Change("creation_order", representationFeatures=[Reference("form_feature")])
    Identity = Author.Roles["form_feature"]
    Author.Change(
        "feature_ids",
        enetityIdMap=[{"key": Identity, "value": [Operation, Operation + 1]}],
        featureIdMap=[
            {"key": Operation, "value": Identity},
            {"key": Operation + 1, "value": Identity},
        ],
    )
    Author.Change("component", operationSeedId=Operation + 2)
    LinkGraphMut(Author)
