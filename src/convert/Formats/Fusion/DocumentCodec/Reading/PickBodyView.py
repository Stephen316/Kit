from collections import Counter as CountValues

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.DocumentCodec.Reading.HistoryShapes import (
    KPrismShape,
    KRotaryShape,
)
from convert.Formats.Fusion.DocumentCodec.Reading.IsInsertHistory import IsInsertHistory


# pick body view must resolve unambiguously so model state retains its native feature and ownership relationships
def PickBodyView(Model: JournalModel) -> str:
    if not IsInsertHistory(Model):
        return "journal"
    Names = CountValues(MakeEntityNode(Value).Name for Value in Model.Entities)
    if Names == KPrismShape:
        return "prism"
    if Names == KRotaryShape:
        Surface = next(Value for Value in Model.Entities if isinstance(Value, ConeNode))
        return "frustum" if Surface.SineAngle != 0 else "cylinder"
    return "journal"
