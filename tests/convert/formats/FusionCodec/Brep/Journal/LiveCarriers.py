from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize


def LiveCarriers(Model: JournalModel) -> tuple[ConeNode, ...]:
    Results: list[ConeNode] = []
    for State in Materialize(Model):
        for _, Revision in State.Versions:
            Value = Model.Entities[Revision]
            if isinstance(Value, ConeNode):
                Results.append(Value)
    return tuple(Results)
