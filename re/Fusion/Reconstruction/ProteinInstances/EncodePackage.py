import io
import runpy
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path


def field(parent, kind, name, value):
    child = ET.SubElement(parent, kind, {"name": name})
    child.text = str(value)


def document(group_name):
    root = ET.Element("root", {"version": "1", "name": "root"})
    group = ET.SubElement(root, "group", {"name": group_name})
    return root, group


def connections(names):
    root, group = document("default")
    for name in names:
        ET.SubElement(group, "link", {"name": name})
    return root


def resources(rows, timestamp):
    root, group = document("default")
    for name, filename, content_type in rows:
        link = ET.SubElement(group, "link", {"name": name, "class": "schema.autodesk.data.1.resource"})
        field(link, "time", "created", timestamp)
        field(link, "bool", "interop%20content", 0)
        field(link, "uri", "name", filename)
        field(link, "string", "type", content_type)
    return root


def core(identifier, timestamp, name=None, package_root=False, embed=None):
    root, group = document("content")
    asset = ET.SubElement(group, "node", {"name": "asset", "class": "schema.autodesk.package.1.asset"})
    field(asset, "time", "created", timestamp)
    if embed is not None:
        field(asset, "uint32", "embed option", embed)
    field(asset, "uuid", "identifier", identifier)
    if name is not None:
        field(asset, "string", "name", name)
    if package_root:
        field(asset, "string", "last saved", "")
        field(asset, "bool", "read only", 0)
    field(asset, "time", "updated", timestamp)
    field(asset, "uint32", "updates", 1)
    return root


def encode_package(materials, schemas, package_id, asset_id, timestamp, encoder=None):
    uuid.UUID(package_id)
    uuid.UUID(asset_id)
    created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if created.tzinfo is None:
        raise ValueError("Material package timestamp requires a timezone")
    for name, schema in schemas.items():
        if not name or any(character in name for character in ("/", "\\", "\0")) or name in (".", ".."):
            raise ValueError("Invalid material schema name")
        if schema.tag != "AssetSchema" or [node.attrib.get("val") for node in schema.findall("UID")] != [name]:
            raise ValueError("Schema UID does not match its name")
        if any(base.attrib["val"] not in schemas for base in schema.findall("Base")):
            raise ValueError("Missing base schema")
    if encoder is None:
        encoder = runpy.run_path(str(Path(__file__).with_name("EncodeMaterials.py")))["encode_material_data"]
    binary = encoder(materials, schemas)
    binary["StreamVersionTable"] = b"AssetTableOfContents:3.1,\nDefinitionIteratorProperties:3.2,\nInstanceProperties:3.2,\nAssetLibVersion:1.0\n"
    asset_prefix = asset_id + "/"
    entries = {asset_prefix + "AssetData/" + name: value for name, value in binary.items()}
    xml = {asset_prefix + "Schemas/" + name + ".xml": schema for name, schema in sorted(schemas.items())}
    xml["cnx.xml"] = connections([asset_id])
    xml[asset_prefix + "cnx.xml"] = connections(["AssetData", "Schemas"])
    xml[asset_prefix + "AssetData/cnx.xml"] = resources([(Path(name).stem, name, "application/octet-stream") for name in sorted(binary)], timestamp)
    xml[asset_prefix + "Schemas/cnx.xml"] = resources([(name, name + ".xml", "application/xml") for name in sorted(schemas)], timestamp)
    xml["core.xml"] = core(package_id, timestamp, package_root=True)
    xml[asset_prefix + "core.xml"] = core(asset_id, timestamp, name=asset_id, embed=49)
    for name in ("AssetData", "Schemas"):
        xml[asset_prefix + name + "/core.xml"] = core(package_id, timestamp, name=name)
    types = ET.Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
    for extension, content_type in (("xml", "application/xml"), ("", "application/octet-stream"), ("bin", "application/octet-stream")):
        ET.SubElement(types, "Default", {"Extension": extension, "ContentType": content_type})
    xml["[Content_Types].xml"] = types
    formats = ET.Element("formats")
    ET.SubElement(formats, "format").text = "http://schema.autodesk.com/design-package/2009"
    xml["autodesk-design-package.xml"] = formats
    entries.update({name: ET.tostring(tree, encoding="utf-8", xml_declaration=True) for name, tree in xml.items()})
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return target.getvalue()
