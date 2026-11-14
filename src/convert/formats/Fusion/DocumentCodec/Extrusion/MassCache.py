from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint
from math import pi as KPiValue


def MassCache(Author: AuthorState) -> list[dict[str, object]]:
    RadiusValue, HeightValue = (
        Author.SpecValue.RadiusMm / 10.0,
        Author.SpecValue.LengthMm / 10.0,
    )
    VolumeValue = KPiValue * RadiusValue * RadiusValue * HeightValue
    Transverse = VolumeValue * (
        RadiusValue * RadiusValue / 4.0 + HeightValue * HeightValue / 3.0
    )
    FieldValues: dict[str, object] = dict(
        area=2.0 * KPiValue * RadiusValue * (RadiusValue + HeightValue),
        areaPrec=0.0,
        cog=MakePoint(0.0, 0.0, HeightValue / 2.0),
        inertiaPrec=0.0,
        moi=MakePoint(
            Transverse, Transverse, VolumeValue * RadiusValue * RadiusValue / 2.0
        ),
        moiOffDiag=MakePoint(),
        revisionGuid="00000000-0000-0000-0000-000000000000",
        volume=VolumeValue,
        volumePrec=0.0,
    )
    return [Author.MakeGroup("MassPropertyCacheValue", FieldValues)]
