from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashContent

from interchange.document.models.DocumentModel import CadDocument
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from tests.interchange.fixtures.DocumentFixture import BuildDocument


# retained payload refusal must cover every declared role including records without embedded bytes
def BuildPayload(RoleValue: PayloadRole, HasData: bool) -> CadDocument:
    Content = b"retained native bytes"
    Payload = BrepPayload(
        "payload:native",
        "fixture.native",
        "native_document",
        "opaque",
        HashContent(Content).hexdigest(),
        Content if HasData else None,
        role=RoleValue,
    )
    return ReplaceData(BuildDocument(), brep_payloads=(Payload,))
