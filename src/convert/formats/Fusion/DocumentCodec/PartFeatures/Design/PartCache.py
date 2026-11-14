from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import SolidMass
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def MakeVector(First: float, Second: float, Third: float) -> dict[str, float]:
    return {"x": First, "y": Second, "z": Third}


def PartCache(Author: AuthorState, Solid: PrismSolid) -> list[dict[str, object]]:
    MassValue = SolidMass(Solid)
    Volume = MassValue["volume"]
    Fields: dict[str, object] = dict(
        area=MassValue["area"],
        areaPrec=0.0,
        cog=MakeVector(
            MassValue["x"] / Volume, MassValue["y"] / Volume, MassValue["z"] / Volume
        ),
        inertiaPrec=0.0,
        moi=MakeVector(
            MassValue["yy"] + MassValue["zz"],
            MassValue["xx"] + MassValue["zz"],
            MassValue["xx"] + MassValue["yy"],
        ),
        moiOffDiag=MakeVector(-MassValue["xy"], -MassValue["xz"], -MassValue["yz"]),
        revisionGuid=Author.RevisionId,
        volume=Volume,
        volumePrec=0.0,
    )
    return [Author.MakeGroup("MassPropertyCacheValue", Fields)]
