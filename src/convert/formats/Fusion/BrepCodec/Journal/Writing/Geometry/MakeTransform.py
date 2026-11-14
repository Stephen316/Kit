from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    IntWord,
    LogicWord,
    RefWord,
    VectorWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeTransform(Value: TransformNode) -> AsmRecord:
    return AsmRecord(
        "transform",
        (
            RefWord(Value.Attribute),
            IntWord(Value.EntityTag),
            VectorWord(Value.ColumnX),
            VectorWord(Value.ColumnY),
            VectorWord(Value.ColumnZ),
            VectorWord(Value.TranslationCm),
            FloatWord(Value.ScaleFactor),
            LogicWord(Value.HasRotation),
            LogicWord(Value.HasReflection),
            LogicWord(Value.HasShear),
        ),
    )
