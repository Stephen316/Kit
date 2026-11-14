from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def TaperParameter(Author: AuthorState) -> dict[str, object]:
    Degrees = Author.SpecValue.TaperDegrees
    Parameter = MakeNumeric("d3", 0.0, "", Author.Policy.ParamBirthday)
    Parameter.update(
        creationIndex=3,
        dcParameter=Author.Reference("taper_binding"),
        expression=(str(Degrees) if Degrees else "0") + " deg",
        isUserDefined=False,
        name="TaperAngle",
        unit="deg",
        value=Radians(Degrees),
    )
    return Parameter
