from io import BytesIO as ByteStream
from zipfile import ZIP_DEFLATED as KZipDeflated, ZipFile


def ChangePackage(Payload: bytes, ModeName: str) -> bytes:
    with ZipFile(ByteStream(Payload)) as Archive:
        Members = {
            NameValue: Archive.read(NameValue) for NameValue in Archive.namelist()
        }
    SchemaName = next(
        NameValue
        for NameValue in Members
        if NameValue.endswith("/Schemas/CommonSchema.xml")
    )
    if ModeName == "extra":
        Members["unmodeled.bin"] = b"unmodeled"
    elif ModeName == "version":
        NameValue = next(
            NameValue
            for NameValue in Members
            if NameValue.endswith("/StreamVersionTable")
        )
        Members[NameValue] += b"UnknownStream:1.0\n"
    elif ModeName == "schema":
        Members[SchemaName] = Members[SchemaName].replace(
            b'val="CommonSchema"', b'val="MissingSchema"'
        )
    elif ModeName == "doctype":
        Members[SchemaName] = Members[SchemaName].replace(
            b"<AssetSchema",
            b'<!DOCTYPE AssetSchema [<!ENTITY value "text">]><AssetSchema',
            1,
        )
    elif ModeName == "resource":
        NameValue = SchemaName.rsplit("/", 1)[0] + "/cnx.xml"
        Members[NameValue] = Members[NameValue].replace(
            b"CommonSchema.xml", b"MissingSchema.xml"
        )
    else:
        raise ValueError("Unknown package mutation")
    Result = ByteStream()
    with ZipFile(Result, "w", compression=KZipDeflated) as Archive:
        for NameValue, Content in Members.items():
            Archive.writestr(NameValue, Content)
    return Result.getvalue()
