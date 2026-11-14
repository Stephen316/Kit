from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import MakeRecord
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KActRecords = (
    MakeRecord(
        0,
        (
            EntityGroup("596618BE-CD74-4BC9-A627-2DA799696C2D", ()),
            EntityGroup(
                "E47053DB-8AF6-4521-81D6-523964C0C97A",
                (
                    NamedValue("rootId", "ACTComponentsRoot"),
                    NamedValue("rooted", ValueSeries((LocalRef(1),))),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F", (NamedValue("rParent", None),)
            ),
        ),
        RootId="ACTComponentsRoot",
    ),
    MakeRecord(
        1,
        (
            EntityGroup(
                "D956D02C-2806-4E57-8B2E-EFA323A5C2B8",
                (
                    NamedValue("ACTInstances", LocalRef(2)),
                    NamedValue("actIdentifier", "1_1"),
                    NamedValue("designComponent", SegmentRef(0, 0)),
                    NamedValue("name", ""),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
                (NamedValue("rParent", LocalRef(4)),),
            ),
        ),
    ),
    MakeRecord(
        2,
        (
            EntityGroup(
                "F01D16CF-95D5-4239-A488-00448AC88023",
                (
                    NamedValue("rDesignInstances", SegmentRef(3, 0)),
                    NamedValue("softDeletedInstances", ValueSeries(())),
                ),
            ),
            EntityGroup(
                "834C9DEF-4C39-4587-A08D-A5BD1267B7B4",
                (NamedValue("children", ValueSeries(())),),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
                (NamedValue("rParent", LocalRef(1)),),
            ),
        ),
    ),
    MakeRecord(
        3,
        (
            EntityGroup(
                "F3E2665C-F3E1-4BA7-8676-8B90579B56D3",
                (
                    NamedValue("instancesMap", ValueMap((ValuePair(0, LocalRef(4)),))),
                    NamedValue("nextInstanceId", 1),
                ),
            ),
            EntityGroup(
                "E47053DB-8AF6-4521-81D6-523964C0C97A",
                (
                    NamedValue("rootId", "ACTInstancesRoot"),
                    NamedValue("rooted", ValueSeries((LocalRef(4),))),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F", (NamedValue("rParent", None),)
            ),
        ),
        RootId="ACTInstancesRoot",
    ),
    MakeRecord(
        4,
        (
            EntityGroup(
                "96E1B59A-1989-4493-AA92-67E6072135F6",
                (
                    NamedValue(
                        "ACTRef",
                        ValueObject(
                            (
                                EntityGroup(
                                    "3AFBE085-BFA1-4DA6-BE71-45A6C61ECB99",
                                    (
                                        NamedValue("actRefdTable", None),
                                        NamedValue(
                                            "changeTypesToTrack",
                                            ValueSeries(
                                                (
                                                    "Appearance",
                                                    "Geometry",
                                                    "PhysicalMaterial",
                                                    "Properties",
                                                    "StructureChange",
                                                    "Transform",
                                                )
                                            ),
                                        ),
                                        NamedValue("crossAsset", False),
                                        NamedValue("owningEntity", LocalRef(4)),
                                        NamedValue("rActData", None),
                                        NamedValue("refdEntity", LocalRef(1)),
                                    ),
                                ),
                            )
                        ),
                    ),
                    NamedValue("actIdentifier", "1_4"),
                    NamedValue("bSoftDeleted", False),
                    NamedValue("designInstance", SegmentRef(20, 0)),
                    NamedValue("instanceId", 0),
                    NamedValue("targetComponent", LocalRef(1)),
                ),
            ),
            EntityGroup(
                "CB844AB6-240D-4fc9-9C9F-3679DC896D6F", (NamedValue("rParent", None),)
            ),
        ),
        RootId="ACTInstanceRoot",
    ),
)
