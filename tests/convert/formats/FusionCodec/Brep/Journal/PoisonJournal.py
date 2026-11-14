from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeStateNode import MakeStateNode


def PoisonJournal(Payload: bytes, Fault: str) -> bytes:
    if Fault == "trailing":
        return Payload + b"unknown"
    if Fault == "attribute":
        return Payload.replace(b"FPM_tracked_attrib_def", b"NEW_tracked_attrib_def", 1)
    Native = ReadJournal(Payload)
    if Fault == "reference":
        Value = next(Value for Value in Native.Entities if isinstance(Value, BodyNode))
        Target = next(
            Index
            for Index, Value in enumerate(Native.Entities)
            if isinstance(Value, PointNode)
        )
        Prior = MakeEntityNode(Value)
        Altered = MakeEntityNode(ReplaceValue(Value, FirstLump=Target))
    elif Fault == "status":
        State = Native.States[0]
        Boards = (ReplaceValue(State.Boards[0], Status=3), *State.Boards[1:])
        Prior, Altered = MakeStateNode(State), MakeStateNode(
            ReplaceValue(State, Boards=Boards)
        )
    elif Fault == "initial-board":
        State = Native.States[Native.Stream.InitialNode]
        Boards = (BulletinBoard(Native.Stream.InitialNode, 2, ()),)
        Prior, Altered = MakeStateNode(State), MakeStateNode(
            ReplaceValue(State, Boards=Boards)
        )
    elif Fault == "cycle":
        State = Native.States[0]
        Prior, Altered = MakeStateNode(State), MakeStateNode(
            ReplaceValue(State, NextNode=0)
        )
    else:
        raise ValueError("Unknown journal fixture mutation")
    return Payload.replace(EmitWireRecord(Prior), EmitWireRecord(Altered), 1)
