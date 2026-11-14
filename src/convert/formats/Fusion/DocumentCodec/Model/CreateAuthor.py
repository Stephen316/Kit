from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas


def CreateAuthor(SpecValue: DocumentSpec, AssetId: str) -> AuthorState:
    Policy = AuthorPolicy()
    Schemas = AuthorSchemas(
        SpecValue.ProfileKind,
        SpecValue.ConstrainRectangle,
        bool(SpecValue.Features),
        any(isinstance(Feature, PasteSpec) for Feature in SpecValue.Features),
    )
    return AuthorState(
        SpecValue,
        Policy,
        AssetId,
        Schemas,
        {Schema.NameValue: Schema for Schema in Schemas},
        {Schema.Value.ClassGuid.upper(): Schema for Schema in Schemas},
        {},
        {},
        [],
        Policy.FirstDesignId,
        str(MakeUuid()),
        str(MakeUuid()),
        str(MakeUuid()),
        str(MakeUuid()),
        "BREP." + str(MakeUuid()) + ".smbh",
    )
