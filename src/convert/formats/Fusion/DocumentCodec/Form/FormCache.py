from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.DocumentCodec.Form.CenteredMass import CenteredMass
from convert.formats.Fusion.DocumentCodec.Form.FormMass import FormMass
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def FormCache(
    Author: AuthorState, Model: FormBody, IsClosed: bool
) -> list[dict[str, object]]:
    MassValue = FormMass(Model, IsClosed)
    Center, Diagonal, Products = (
        CenteredMass(MassValue) if IsClosed else (MakePoint(), MakePoint(), MakePoint())
    )
    Fields: dict[str, object] = dict(
        area=MassValue["area"],
        areaPrec=0.0,
        cog=Center,
        inertiaPrec=0.0,
        moi=Diagonal,
        moiOffDiag=Products,
        revisionGuid=Author.RevisionId,
        volume=MassValue["volume"],
        volumePrec=0.0,
    )
    return [Author.MakeGroup("MassPropertyCacheValue", Fields)]
