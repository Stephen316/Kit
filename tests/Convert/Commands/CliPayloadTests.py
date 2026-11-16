from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.Payloads.PayloadRoles import PayloadRole
from tests.Convert.Commands.BuildPayload import BuildPayload
from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.WrapDocument import WrapDocument


# retained payload declarations must block conversion regardless of role nesting or embedded data
@TestMark.parametrize("RoleValue", tuple(PayloadRole))
@TestMark.parametrize("HasData", (False, True))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPayload(
    RoleValue: PayloadRole,
    HasData: bool,
    IsNested: bool,
    HasOutput: bool,
    TmpPath: FilePath,
) -> None:
    Document = BuildPayload(RoleValue, HasData)
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "RetainedPayload", HasOutput, TmpPath)
