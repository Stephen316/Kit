from json import loads as LoadJson
from typing import TypedDict, cast as CastValue

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip


class RoleValue(TypedDict):
    value: str
    dataType: str


class ReferenceRow(TypedDict):
    relativePath: str
    properties: list[dict[str, RoleValue]]


class RedirectRows(TypedDict):
    references: list[ReferenceRow]


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
