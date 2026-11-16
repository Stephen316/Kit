# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify freshly rendered preview pixels against independent licensed geometry."""

from hashlib import sha256
from itertools import product
import json
from pathlib import PurePosixPath

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require

from PartPreview import (
    DIB_SIZE,
    PNG_SIZE,
    BuildPreviewDrawing,
    DrawPreview,
    FitFaces,
    Palette,
    PreviewDrawing,
    RenderPartPreview,
)
from RectangleCorners import CornerPoint
from VerifyBossOpen import verify_measured
from VerifyModelHeader import measured_bounds
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart

# the demonstration has no connection to vendor palette or material colors
DEMO_COLORS: Palette = ((248, 248, 248), (35, 35, 35), (176, 176, 176))


# the archive reader supplies the diagram while licensed measurements check it
def ReadDrawing(Archive, Native, Generation: int) -> PreviewDrawing:
    Model = ReadRectPart(
        Archive.require(KConfigStream),
        Archive.require(KResolvedFeaturesStream),
        Generation,
    )
    Geometry = Model.Profile.Geometry
    Corners = tuple(
        CornerPoint(Index, tuple(Value), 0)
        for Index, Value in enumerate(Geometry["points_metres"][:4], 1)
    )
    Edges = {
        Row["native_id"]: tuple(Row["point_indices"])
        for Row in Geometry["lines"]
        if Row["native_id"] > 0
    }
    Depth = None
    if Model.Boss is not None:
        verify_measured(Model.Boss, Native)
        Dimension = Model.Boss["depth_display"]["dimension"]["metres"]
        Depth = (
            -Dimension
            if Model.Boss["end_specification"]["direction"] == 1
            else Dimension
        )
    return BuildPreviewDrawing(Model.Reference.FeatureId, Corners, Edges, Depth)


# licensed world edges and solid bounds establish sketch and face geometry independently
def CheckDrawing(Drawing: PreviewDrawing, Native) -> None:
    def Normalise(Point):
        return tuple(round(Field, 11) for Field in Point)

    (Profile,) = tuple(
        Row for Row in Native["sketches"] if Row["name"] == "RectangleSketch"
    )
    NativeEdges = {
        frozenset(
            Normalise(Value / 1000 for Value in Row[Point])
            for Point in ("start_world_mm", "end_world_mm")
        )
        for Row in Profile["entities"]
        if not Row["construction"]
    }
    DrawingEdges = {
        frozenset((Normalise(A), Normalise(B)))
        for A, B in zip(Drawing.Base, (*Drawing.Base[1:], Drawing.Base[0]), strict=True)
    }
    require(
        len(DrawingEdges) == 4 and DrawingEdges == NativeEdges,
        "same licensed world outline",
    )
    require(int(Drawing.Solid) == Native["body_count"], "same licensed body count")
    if not Drawing.Solid:
        require(Drawing.Faces == (Drawing.Base,), "body-free outline")
        return
    Bounds = measured_bounds(Native)
    Maximum = Normalise(Bounds.Maximum)
    Vertices = set(product(*zip(Normalise(Bounds.Minimum), Maximum, strict=True)))
    Expected = {
        frozenset(P for P in Vertices if P[Axis] == Maximum[Axis]) for Axis in range(3)
    }
    Drawn = {frozenset(map(Normalise, Face)) for Face in Drawing.Faces}
    require(
        len(Drawn) == 3 and Drawn == Expected,
        "exact visible cap and two sides of signed licensed boss",
    )


# visible face vertices and centers distinguish outline and surface coverage
def CheckRasterGeometry(
    Drawing: PreviewDrawing, Indexed: bytes, Width: int, Height: int
) -> None:
    for Face in FitFaces(Drawing, Width, Height):
        require(
            all(Indexed[Y * Width + X] == 1 for X, Y in Face),
            "every projected visible face vertex has ink",
        )
        CenterX = sum(X for X, _ in Face) // 4
        CenterY = sum(Y for _, Y in Face) // 4
        require(
            Indexed[CenterY * Width + CenterX] == (2 if Drawing.Solid else 0),
            "every projected face center is filled only for a solid",
        )


# the two representations follow the same pixel-index and explicit color contract
def CheckImages(Drawing: PreviewDrawing, Generation: int) -> dict[str, str]:
    Raster = RenderPartPreview(Generation, Drawing, DEMO_COLORS)
    Indices = DrawPreview(Drawing, *PNG_SIZE)
    Colors = tuple(bytes((*Rgb, 255)) for Rgb in DEMO_COLORS)
    require(
        len(Raster.DibIndices) == DIB_SIZE[0] * DIB_SIZE[1]
        and len(Raster.PngRgba) == PNG_SIZE[0] * PNG_SIZE[1] * 4
        and set(Raster.DibIndices)
        == set(Indices)
        == set(range(3 if Drawing.Solid else 2))
        and Raster.PngRgba == b"".join(Colors[Index] for Index in Indices),
        "two canvases preserve the intended outline and solid fill",
    )
    CheckRasterGeometry(Drawing, Raster.DibIndices, *DIB_SIZE)
    CheckRasterGeometry(Drawing, Indices, *PNG_SIZE)
    return {
        "dib_indices": sha256(Raster.DibIndices).hexdigest(),
        "png_rgba": sha256(Raster.PngRgba).hexdigest(),
    }


# the renderer refuses contradictory geometry and presentation inputs
def CheckRefusals() -> int:
    Rectangle = (
        CornerPoint(1, (0.0, 0.0), 0),
        CornerPoint(2, (0.04, 0.0), 0),
        CornerPoint(3, (0.04, 0.02), 0),
        CornerPoint(4, (0.0, 0.02), 0),
    )
    Edges = {1: (0, 1), 2: (1, 2), 3: (2, 3), 4: (3, 0)}
    Drawing = BuildPreviewDrawing(2, Rectangle, Edges, 0.01)
    OtherColors: Palette = ((255, 255, 255), (0, 0, 0), (127, 127, 127))
    Chosen = RenderPartPreview(19000, Drawing, DEMO_COLORS)
    Other = RenderPartPreview(19000, Drawing, OtherColors)
    require(
        Chosen.DibIndices == Other.DibIndices
        and Chosen.PngRgba != Other.PngRgba
        and set(Other.PngRgba[3::4]) == {255},
        "caller color policy leaves the geometry raster unchanged",
    )
    Controls = (
        (BuildPreviewDrawing, (3, Rectangle, Edges, 0.01)),
        (BuildPreviewDrawing, (2, Rectangle, {**Edges, 1: (0, 2)}, 0.01)),
        (BuildPreviewDrawing, (2, Rectangle, Edges, 0.0)),
        (BuildPreviewDrawing, (2, Rectangle, Edges, float("nan"))),
        (RenderPartPreview, (18000, Drawing, DEMO_COLORS)),
        (RenderPartPreview, (19000, Drawing, (DEMO_COLORS[0],) * 3)),
    )
    for Operation, Args in Controls:
        try:
            Operation(*Args)
        except ValueError:
            continue
        raise ValueError("ordinary renderer accepted invalid input")
    return len(Controls)


# source bindings name only the persisted model geometry rather than the saved pixels
def InspectCapture(Recipe, Asset, Source, Native):
    Archive = SldprtArchive.from_bytes(Source, Asset["path"])
    Generation = ContainerMo(Archive.streams)
    require(Generation == 19000, "ordinary principal preview generation")
    Drawing = ReadDrawing(Archive, Native, Generation)
    CheckDrawing(Drawing, Native)
    return {
        "recipe": Recipe,
        "variant": PurePosixPath(Asset["path"]).stem.removeprefix(
            f"{Recipe}-solidworks-"
        ),
        "raster": CheckImages(Drawing, Generation),
        "visible_faces": len(Drawing.Faces) if Drawing.Solid else 0,
    }


# independently authored repeats and unit variants have identical geometric pixels
def CheckVariants(Rows) -> None:
    for Family, Count in (("P01", 6), ("P03", 8)):
        Cases = {Row["variant"]: Row for Row in Rows if Row["recipe"] == Family}
        require(len(Cases) == Count, "complete sealed variant roster")
        for Name in ("dib_indices", "png_rgba"):
            Images = {Key: Row["raster"][Name] for Key, Row in Cases.items()}
            Base = Images.pop("baseline-a")
            require(
                Images.pop("baseline-b") == Images.pop("units-inch") == Base,
                "invariant geometry and units",
            )
            require(
                len({Base, *Images.values()}) == Count - 2,
                "typed shape edits and datum produce distinct previews",
            )


# repeatable report publishes digests only and never forwards archive pixels
def Report() -> dict[str, object]:
    NegativeControls = CheckRefusals()
    Cases = {
        Asset["sha256"]: InspectCapture(Recipe, Asset, Source, Native)
        for Recipe, Asset, Source, _, Native in principal_captures()
    }
    CheckVariants(Cases.values())
    return {
        "capture_revision": CAPTURE_REVISION,
        "cases": Cases,
        "negative_controls": NegativeControls,
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
