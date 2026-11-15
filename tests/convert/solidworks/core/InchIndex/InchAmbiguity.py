from tests.convert.solidworks.core.InchIndex.OwnerFrame import OwnerFrame
from tests.convert.solidworks.core.InchIndex.ScalarFrame import ScalarFrame


def InchAmbiguity() -> tuple[bytes, bytes]:
    Scalars = (
        ("Duplicate", 0.001, 1000, 0),
        ("Duplicate", 0.002, 1001, 0),
        ("NoIdentity", 0.001, None, 0),
        ("DisplayOnly", 0.001, 1002, 1),
        ("WrongRound", 0.02, 1003, 0),
        ("Precision", 0.001, 1004, 0),
        ("TrailingZero", 0.001, 1007, 0),
        ("Valid", 0.001, 1005, 0),
        ("NativeRole", 0.001, 1006, 2),
        ("ZeroIdentity", 0.001, 0, 0),
    )
    Dimensions = "".join(
        f'<Dimension Name="{NameValue}">{"0.041" if NameValue == "Precision" else "0.040" if NameValue == "TrailingZero" else "0.04"}</Dimension>'
        for NameValue in dict.fromkeys(Scalar[0] for Scalar in Scalars)
    )
    Keywords = f'<Root><Feature id="20" Name="Owned" Type="Datum">{Dimensions}</Feature></Root>'
    Resolved = OwnerFrame("Owned", 20) + b"".join(
        ScalarFrame(*Scalar) for Scalar in Scalars
    )
    return Keywords.encode("utf-8"), Resolved
