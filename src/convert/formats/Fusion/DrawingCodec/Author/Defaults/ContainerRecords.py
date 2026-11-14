from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import (
    ChildTail,
    MakeRecord,
)
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KContainerRecords = (
    MakeRecord(
        1,
        (
            EntityGroup(
                "BC84911E-A581-4E51-ABE4-B0F681CFED06",
                (
                    NamedValue("creationIndex", 0),
                    NamedValue("externalCreationIndex", 0),
                ),
            ),
            EntityGroup("5EAF2F0F-4AEE-4f20-B569-119A7BD1F36D", ()),
            EntityGroup(
                "E47053DB-8AF6-4521-81D6-523964C0C97A",
                (
                    NamedValue("rootId", "ComponentsRoot"),
                    NamedValue("rooted", ValueSeries((LocalRef(0),))),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F", (NamedValue("rParent", None),)
            ),
        ),
        RootId="ComponentsRoot",
    ),
    MakeRecord(
        2,
        (
            EntityGroup("F9CB8717-EB86-47F2-AAA7-39E142C57A09", ()),
            EntityGroup(
                "834C9DEF-4C39-4587-A08D-A5BD1267B7B4",
                (NamedValue("children", ValueSeries(())),),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
                (NamedValue("rParent", LocalRef(0)),),
            ),
        ),
    ),
    MakeRecord(
        3,
        (
            EntityGroup("904F885E-D859-4755-A7EF-6EBED8732FAD", ()),
            EntityGroup(
                "21F379C8-CAFD-4985-B461-767673A4C502",
                (NamedValue("rACTInstances", SegmentRef(2, 1)),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        4,
        (
            EntityGroup(
                "CD57BC48-50EC-47DC-975A-FB6DEA72F4DA",
                (
                    NamedValue("alterateBodies", False),
                    NamedValue("creationIndex", 0),
                    NamedValue("groupChildren", ValueSeries(())),
                    NamedValue("isVisible", True),
                    NamedValue("passiveIdGenerator", None),
                    NamedValue("rBRepSerializer", LocalRef(5)),
                    NamedValue("selectable", True),
                    NamedValue("surfaceGroups", LocalRef(16)),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        5,
        (
            EntityGroup(
                "40DCC3F41D-E94F-B3B1-3E95-9B6ABE572C",
                (NamedValue("topEntityPIDGenerator", LocalRef(6)),),
            ),
            EntityGroup(
                "E8DCB040-6A0E-4AD1-BCF3-1E1AEDD35EE4",
                (
                    NamedValue("mapBodyId", ValueMap(())),
                    NamedValue("rBodies", LocalRef(4)),
                    NamedValue("rBody", None),
                ),
            ),
            EntityGroup(
                "130A0711-4E92-4FCD-AADE-B9C82238BB27", (NamedValue("partName", ""),)
            ),
        ),
    ),
    MakeRecord(
        6,
        (
            EntityGroup(
                "E55D0457-898F-4A8E-B1A5-C85BDBA8794F",
                (
                    NamedValue("addressOfTopEntities", ValueSeries(())),
                    NamedValue("nextId", 0),
                    NamedValue("rBodies", None),
                    NamedValue("rBody", None),
                    NamedValue("scanOrderIndex", ValueSeries(())),
                ),
            ),
        ),
    ),
    MakeRecord(
        7,
        (
            EntityGroup(
                "5275CBA4-3D7D-40DC-A651-1DFF3FC8AFBF",
                (
                    NamedValue("groupChildren", ValueSeries(())),
                    NamedValue("highWaterMark", 0),
                    NamedValue("isVisible", True),
                    NamedValue("selectable", True),
                    NamedValue("sketchCustomGroups", LocalRef(19)),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        8,
        (
            EntityGroup(
                "A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E",
                (
                    NamedValue("groupChildren", ValueSeries(())),
                    NamedValue("highWaterMarkAxes", 0),
                    NamedValue("highWaterMarkPlanes", 0),
                    NamedValue("highWaterMarkPoints", 0),
                    NamedValue("highWaterMarkUCS", 0),
                    NamedValue("isVisible", True),
                    NamedValue("selectable", True),
                    NamedValue("workGeometryCustomGroups", LocalRef(18)),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        9,
        (
            EntityGroup(
                "FCB17D75-8538-4E8E-BDBE-CB4FE2120DB7",
                (
                    NamedValue("highWaterMark", 0),
                    NamedValue("visible", True),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        10,
        (
            EntityGroup(
                "596C8B98-D176-4E40-B294-6404BAD566BC",
                (
                    NamedValue("constraintsHighWaterMark", 0),
                    NamedValue("highWaterMark", 0),
                    NamedValue("isVisible", True),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        11,
        (
            EntityGroup(
                "AC202226-A700-462A-BC41-13631C9E95D5",
                (NamedValue("highWaterMark", 0),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        12,
        (
            EntityGroup(
                "0DBF95ED-82D2-4CC4-936D-642370679CBB",
                (
                    NamedValue("highWaterMark", 0),
                    NamedValue("mode", 0),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        13,
        (
            EntityGroup(
                "77EF6384-409E-498D-8167-BCA537533B35",
                (NamedValue("highWaterMark", 0),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        14,
        (
            EntityGroup(
                "B0556F58-EE09-46A7-B18F-E296F48E5B13",
                (
                    NamedValue("bIsStateChangedByUser", False),
                    NamedValue("expandedNodeSet", ValueSeries(())),
                    NamedValue("groupOrder", ValueSeries(())),
                    NamedValue("highWaterMark", 0),
                    NamedValue("rParameterSearchByNameHelper", LocalRef(15)),
                ),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        15,
        (
            EntityGroup(
                "E276745D-D84E-40D5-88BC-8C94DD4ACCDF",
                (NamedValue("parameterMap", ValueMap(())),),
            ),
        ),
        Subjects=(SubjectValue(LocalRef(14), 0),),
    ),
    MakeRecord(
        16,
        (
            EntityGroup(
                "372234A0-2A6C-4122-8047-E74DBA04F326",
                (NamedValue("rUnstitchedGroup", None),),
            ),
            EntityGroup(
                "B5B50E5B-EDC8-4309-82A3-C53B3E82033D",
                (NamedValue("highWaterMark", 0),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        17,
        (
            EntityGroup(
                "30DCFC57-8E13-405B-9295-5CF74AC1FB39", (NamedValue("waterMark", 0),)
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        18,
        (
            EntityGroup("47C245A2-2DBE-4B1F-9C56-762F373BB0C8", ()),
            EntityGroup(
                "B5B50E5B-EDC8-4309-82A3-C53B3E82033D",
                (NamedValue("highWaterMark", 0),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        19,
        (
            EntityGroup("0C5DAB90-715E-49EA-A56E-E30F2328F43E", ()),
            EntityGroup(
                "B5B50E5B-EDC8-4309-82A3-C53B3E82033D",
                (NamedValue("highWaterMark", 0),),
            ),
            *ChildTail(LocalRef(0)),
        ),
    ),
    MakeRecord(
        21,
        (
            EntityGroup("D50DCC35-42CC-4E7D-9B81-4EB8252712D0", ()),
            EntityGroup("5EAF2F0F-4AEE-4f20-B569-119A7BD1F36D", ()),
            EntityGroup(
                "E47053DB-8AF6-4521-81D6-523964C0C97A",
                (
                    NamedValue("rootId", "ComponentInstancesRoot"),
                    NamedValue("rooted", ValueSeries((LocalRef(20),))),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F", (NamedValue("rParent", None),)
            ),
        ),
        RootId="ComponentInstancesRoot",
    ),
    MakeRecord(
        23,
        (
            EntityGroup(
                "8F05428E-590E-4DE6-9CEF-B34EDA0D27B9",
                (
                    NamedValue("iGenericModelVersion", 0),
                    NamedValue("rECADModelSources", None),
                    NamedValue("rModelSources", LocalRef(25)),
                    NamedValue("rSheets", LocalRef(26)),
                    NamedValue("rTrackedEntitys", LocalRef(24)),
                    NamedValue("updateOperationIds", False),
                ),
            ),
        ),
        RootId="FDExternalFileRefs",
    ),
    MakeRecord(24, (EntityGroup("981E7978-171B-445C-9533-8401DB6665FE", ()),)),
    MakeRecord(
        36,
        (
            EntityGroup(
                "35899357-B223-4909-AB50-841E9C212694",
                (
                    NamedValue(
                        "FusionDocDesignIdANdMassUnitsPrecisionsInfo", ValueMap(())
                    ),
                ),
            ),
        ),
        RootId="AssetSettings",
    ),
    MakeRecord(
        36,
        (
            EntityGroup(
                "23FD63FB-4EBE-4c85-A42B-5D9809AA3499",
                (
                    NamedValue("ViewPortsDim", ValueSeries(())),
                    NamedValue("activeUnitSystem", None),
                    NamedValue("assetSubType", 0),
                    NamedValue("bSceneUpBlank", False),
                    NamedValue("curDisplayViewPorts", ""),
                    NamedValue("currHomeExtentsHeight", 10.0),
                    NamedValue("currHomeExtentsWidth", 10.0),
                    NamedValue(
                        "currHomePos",
                        ValueStruct(
                            (
                                NamedValue("x", 1.0),
                                NamedValue("y", -1.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("currHomeProjection", 1),
                    NamedValue(
                        "currHomeTarget",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 0.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "currHomeUp",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("currentProjection", 1),
                    NamedValue("defaultHomeExtentsHeight", 10.0),
                    NamedValue("defaultHomeExtentsWidth", 10.0),
                    NamedValue(
                        "defaultHomePos",
                        ValueStruct(
                            (
                                NamedValue("x", 1.0),
                                NamedValue("y", -1.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("defaultHomeProjection", 1),
                    NamedValue(
                        "defaultHomeTarget",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 0.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "defaultHomeUp",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "defaultSceneFront",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 1.0),
                                NamedValue("z", 0.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "defaultSceneUp",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("enableLayoutGridFadeAppearance", False),
                    NamedValue("fitHome", True),
                    NamedValue("globalBoundRadius", 1.8),
                    NamedValue("globalVisibilityOverride", ValueSeries(())),
                    NamedValue("groundPlaneOffset", 0.0),
                    NamedValue("layoutGridDimensionApp", 0),
                    NamedValue("lockGroundPlane", False),
                    NamedValue("lockedGroundPlaneOffset", 0.0),
                    NamedValue(
                        "lockedGroundPlaneOrientation",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("locktoSelection", False),
                    NamedValue("namedViews", None),
                    NamedValue("perspWithOrthoFaces", False),
                    NamedValue("pmiSettings", None),
                    NamedValue("preferredEnvironment", ""),
                    NamedValue("rNamedLights", None),
                    NamedValue("renderSetting", None),
                    NamedValue(
                        "sceneBoundBoxCenter",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 0.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "sceneBoundBoxExtent",
                        ValueStruct(
                            (
                                NamedValue("x", 1.8),
                                NamedValue("y", 1.8),
                                NamedValue("z", 1.8),
                            )
                        ),
                    ),
                    NamedValue("sceneBoundRadius", 1.8),
                    NamedValue(
                        "sceneFront",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 1.0),
                                NamedValue("z", 0.0),
                            )
                        ),
                    ),
                    NamedValue(
                        "sceneUp",
                        ValueStruct(
                            (
                                NamedValue("x", 0.0),
                                NamedValue("y", 0.0),
                                NamedValue("z", 1.0),
                            )
                        ),
                    ),
                    NamedValue("settingsInitialized", False),
                    NamedValue("threadSettings", LocalRef(38)),
                ),
            ),
            EntityGroup("3C822807-C6B1-4ffc-9AE4-769A487EC7B3", ()),
        ),
        RootId="AssetSettings",
        IsPrimary=False,
    ),
    MakeRecord(
        37,
        (
            EntityGroup(
                "2C54F6D6-5C2B-4C4A-89A2-2AB486EF152D",
                (
                    NamedValue("PhysicalMaterialAssetReferences", ValueSeries(())),
                    NamedValue("PhysicalMaterialRefCountVector", ValueSeries(())),
                    NamedValue("VisualMaterialAssetReferences", ValueSeries(())),
                    NamedValue("VisualMaterialRefCountVector", ValueSeries(())),
                ),
            ),
            EntityGroup(
                "130A0711-4E92-4FCD-AADE-B9C82238BB27", (NamedValue("partName", ""),)
            ),
        ),
        RootId="ProteinAssetManager",
    ),
    MakeRecord(
        38,
        (
            EntityGroup(
                "3B9288E7-E1DE-414D-90BD-1C0CDAC77EB1",
                (NamedValue("bModeledThread", False),),
            ),
        ),
    ),
)
