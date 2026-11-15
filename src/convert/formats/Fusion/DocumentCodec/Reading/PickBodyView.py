from collections import Counter as CountValues

from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.DocumentCodec.Reading.HistoryShapes import (
    KPrismShape,
    KRotaryShape,
)
from convert.formats.Fusion.DocumentCodec.Reading.IsInsertHistory import IsInsertHistory


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
