from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


# the list programs contract needs a shared interpretation so topology changes retain their native revision relationships
def ListPrograms(Entities: tuple[KJournalEntity, ...]) -> tuple[TsplineSurface, ...]:
    return tuple(
        Support.Subtrans.Surface
        for Support in ListTsplines(Entities)
        if isinstance(Support.Subtrans, SubtransNode)
    )
