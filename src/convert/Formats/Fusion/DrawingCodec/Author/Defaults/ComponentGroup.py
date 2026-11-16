from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

# component group must remain consistent across callers so sheet objects retain their intended document relationships
KComponentGroup = EntityGroup(
    "42054630-20A0-40E1-B969-CFE9E742F5C9",
    (
        NamedValue("m_SketchCustomGroups", LocalRef(19)),
        NamedValue("m_WorkGeometryCustomGroups", LocalRef(18)),
        NamedValue(
            "massProperties",
            ValueObject(
                (
                    EntityGroup(
                        "98F3955C-FE39-404A-8724-36D0C15A456C",
                        (
                            NamedValue("areaOverride", -1.0),
                            NamedValue("densityOverride", -1.0),
                            NamedValue("massOverride", -1.0),
                            NamedValue("volumeOverride", -1.0),
                        ),
                    ),
                )
            ),
        ),
        NamedValue("rAssyConstraintOccs", LocalRef(11)),
        NamedValue("rAssyConstraints", LocalRef(10)),
        NamedValue("rBodies", LocalRef(4)),
        NamedValue("rContactSets", LocalRef(12)),
        NamedValue("rJointOrigins", LocalRef(9)),
        NamedValue("rMotionStudies", LocalRef(13)),
        NamedValue("rParameterTable", LocalRef(14)),
        NamedValue("rPersistedCustomGraphics", None),
        NamedValue("rSelectionGroups", LocalRef(17)),
        NamedValue("rSketches", LocalRef(7)),
        NamedValue("rSurfaceGroups", LocalRef(16)),
        NamedValue("rWorkGeometries", LocalRef(8)),
    ),
)
