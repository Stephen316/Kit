from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def AddGeometryMut(Author: AuthorState) -> None:
    Author.Allocate(
        "origin_point", "WorkPoint", ParentRole="origin", Fields={"originName": "O"}
    )
    AxisRows = [
        ("x_axis", "X", MakePoint(1.0)),
        ("y_axis", "Y", MakePoint(0.0, 1.0)),
        ("z_axis", "Z", MakePoint(0.0, 0.0, 1.0)),
    ]
    for RoleName, NameValue, Direction in AxisRows:
        Author.Allocate(
            RoleName,
            "WorkAxis",
            ParentRole="origin",
            Fields={
                "originName": NameValue,
                "line": {"pointOnLine": MakePoint(), "parametricDirection": Direction},
            },
        )
    for RoleName, NameValue, AxisFirst, AxisSecond in [
        ("xy_plane", "XY", MakePoint(1.0), MakePoint(0.0, 1.0)),
        ("xz_plane", "XZ", MakePoint(0.0, 0.0, 1.0), MakePoint(1.0)),
        ("yz_plane", "YZ", MakePoint(0.0, 1.0), MakePoint(0.0, 0.0, 1.0)),
    ]:
        Author.Allocate(
            RoleName,
            "WorkPlane",
            ParentRole="origin",
            Fields={
                "originName": NameValue,
                "plane": {
                    "normalReversed": False,
                    "origin": MakePoint(),
                    "uAxis": AxisFirst,
                    "vAxis": AxisSecond,
                },
            },
        )
