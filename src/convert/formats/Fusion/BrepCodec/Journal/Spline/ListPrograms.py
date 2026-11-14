from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def ListPrograms(Entities: tuple[KJournalEntity, ...]) -> tuple[TsplineSurface, ...]:
    return tuple(
        Support.Subtrans.Surface
        for Support in ListTsplines(Entities)
        if isinstance(Support.Subtrans, SubtransNode)
    )
