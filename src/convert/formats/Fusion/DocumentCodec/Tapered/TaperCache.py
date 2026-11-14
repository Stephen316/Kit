from math import hypot as Hypot, pi as KPiValue

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Tapered.TaperModel import TaperModel
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def TaperCache(Author: AuthorState) -> list[dict[str, object]]:
    Model = TaperModel(Author.SpecValue)
    Lower, Upper, Height = (
        Model.BottomRadius / 10.0,
        Model.TopRadius / 10.0,
        Model.Height / 10.0,
    )
    CrossSum = Lower * Lower + Lower * Upper + Upper * Upper
    Delta = Upper - Lower
    Fourth = (
        Height * sum(Lower ** (4 - Index) * Upper**Index for Index in range(5)) / 5.0
    )
    Axial = Height**3 * (Lower**2 / 3.0 + Lower * Delta / 2.0 + Delta**2 / 5.0)
    Transverse = KPiValue * (Fourth / 4.0 + Axial)
    Fields: dict[str, object] = dict(
        area=KPiValue * (Lower**2 + Upper**2 + (Lower + Upper) * Hypot(Height, Delta)),
        areaPrec=0.0,
        cog=MakePoint(
            0.0,
            0.0,
            Height * (Lower**2 + 2 * Lower * Upper + 3 * Upper**2) / (4 * CrossSum),
        ),
        inertiaPrec=0.0,
        moi=MakePoint(Transverse, Transverse, KPiValue * Fourth / 2.0),
        moiOffDiag=MakePoint(),
        revisionGuid=Author.RevisionId,
        volume=KPiValue * Height * CrossSum / 3.0,
        volumePrec=0.0,
    )
    return [Author.MakeGroup("MassPropertyCacheValue", Fields)]
