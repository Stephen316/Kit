from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject
from convert.formats.Fusion.BundleCodec.Validation.CheckModel import CheckModel
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing


def DrawingObject(Description: BundleModel) -> BundleObject:
    CheckModel(Description)
    Owners = {Entry.ObjectId: Entry for Entry in Description.Graph.Objects}
    RootValue = Owners[Description.Graph.RootIds[0]]
    if RootValue.ContentType != "f2d":
        raise ValueError("Fusion drawing bundle root must be an F2D document")
    return RootValue


def CheckBundle(Description: BundleModel, Drawing: FusionDrawing) -> None:
    RootValue = DrawingObject(Description)
    Bundled = {
        Field.TextValue[:36]
        for Group in RootValue.References
        if Group.KindValue == "DERIVED"
        for Relation in Group.Relations
        for Field in Relation.Metadata
        if Field.FieldName == "neutronRole"
    }
    Declared = {LinkValue.Role[:36] for LinkValue in Drawing.Root.References}
    if Bundled != Declared:
        raise ValueError("Fusion drawing references disagree with the bundle graph")
