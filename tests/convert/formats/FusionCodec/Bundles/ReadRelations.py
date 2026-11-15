from json import loads as LoadJson
from typing import TypedDict, cast as CastValue

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip


# the role value boundary needs grouped coverage so repository automation cannot silently change its observable contract
class RoleValue(TypedDict):
    value: str
    dataType: str


# the reference row boundary needs grouped coverage so repository automation cannot silently change its observable contract
class ReferenceRow(TypedDict):
    relativePath: str
    properties: list[dict[str, RoleValue]]


# the redirect rows boundary needs grouped coverage so repository automation cannot silently change its observable contract
class RedirectRows(TypedDict):
    references: list[ReferenceRow]


# shared read relations setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadRelations(DataValue: bytes) -> set[tuple[str, str]]:
    with OpenFusionZip(DataValue) as Archive:
        Payload = Archive.ReadMember("RedirectionsStream.dat", 4 * 1024 * 1024)
    Model = CastValue(RedirectRows, LoadJson(Payload))
    return {
        (Entry["relativePath"], Fields["neutronRole"]["value"])
        for Entry in Model["references"]
        for Fields in Entry["properties"]
        if "neutronRole" in Fields
    }
