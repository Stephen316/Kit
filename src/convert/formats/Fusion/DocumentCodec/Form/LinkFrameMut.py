from convert.formats.Fusion.DocumentCodec.Form.AddFormMut import (
    FrameCounts,
    KFrameKinds,
)
from convert.formats.Fusion.DocumentCodec.Form.FormParts import FormParts
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def FacetMaterial(Author: AuthorState) -> list[dict[str, object]]:
    return [
        Author.MakeGroup(
            "VisualMaterialValue",
            dict(
                CustomizedColor={"red": 0.0, "green": 0.0, "blue": 0.0, "alpha": 1.0},
                ProteinAssetManager=None,
                UseCustomizedColor=False,
                assetReference="",
                libraryID="",
                name="",
                proteinMaterialID="",
                proteinMaterialRotation=0.0,
                proteinMaterialScale=1.0,
            ),
        )
    ]


def LinkFrameMut(Author: AuthorState, SpecValue: FormSpec, Parts: FormParts) -> None:
    Reference = Author.Reference
    Members: dict[str, object] = {}
    for (KindName, _), Count in zip(KFrameKinds, FrameCounts(SpecValue)):
        RoleNames = [f"form_{KindName}_{Index}" for Index in range(Count)]
        Members[KindName + "s" if KindName != "vertex" else "vertices"] = [
            Reference(RoleName) for RoleName in RoleNames
        ]
        for Index, RoleName in enumerate(RoleNames):
            Author.Change(RoleName, rMesh=Reference("form_frame"), tsID=Index)
            if KindName == "facet":
                Author.Change(RoleName, visualMaterial=FacetMaterial(Author))
    Author.Change("form_frame", rSurface=Reference("form_surface"), **Members)
    Author.Change(
        "form_surface",
        rSerializer=Reference("form_serializer"),
        frame=Reference("form_frame"),
        rVSurface=Reference("form_node"),
        tess=Reference("form_tessellation"),
    )
    Author.Change(
        "form_serializer", partName=Parts.Cage, rSurface=Reference("form_surface")
    )
    Author.Change(
        "form_node",
        rDcTSplineFeature=Reference("form_feature"),
        rGroupParent=Reference("cache_bodies"),
        rSurface=Reference("form_surface"),
    )
