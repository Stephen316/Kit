from collections.abc import Mapping, Sequence
from dataclasses import asdict
from hashlib import sha256
from typing import Any, cast
from xml.etree.ElementTree import Element

from convert.formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import (
    KConnectMode,
    KPropertyKind,
    PropertySpec,
)
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import (
    KMaterialValue,
    KScalarValue,
    PropertyValue,
)
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas


def schema_models(schemas: Mapping[str, Element]) -> tuple[MaterialSchema, ...]:
    result = []
    for name, node in schemas.items():
        if node.tag != "AssetSchema" or [item.attrib.get("val") for item in node.findall("UID")] != [name]:
            raise ValueError("Material schema UID differs from the supplied schema identity")
        properties = tuple(
            PropertySpec(
                item.attrib["id"],
                cast(KPropertyKind, item.tag),
                item.attrib.get("definitionIteratorData") == "true",
                item.attrib.get("readonly") == "true",
                item.attrib.get("allowmultiplevalues") == "true",
                item.attrib.get("unit"),
                cast(KConnectMode, item.attrib.get("allowconnectedassets", "none")),
            )
            for item in node
            if "id" in item.attrib
        )
        result.append(MaterialSchema(name, tuple(item.attrib["val"] for item in node.findall("Base")), properties))
    return tuple(result)


def scalar_model(value: Any, spec: PropertySpec) -> KScalarValue:
    if spec.ValueKind == "Float" and spec.UnitName is not None:
        if type(value) is not dict or set(value) != {"unit_code", "value"}:
            raise ValueError("Material unit scalar requires its numeric code and magnitude")
        return UnitValue(value["unit_code"], value["value"])
    if spec.ValueKind == "Color":
        if type(value) not in (tuple, list) or len(value) != 4:
            raise ValueError("Material color requires four RGBA channel values")
        return ColorValue(*value)
    return cast(KScalarValue, value)


def value_model(value: Any, spec: PropertySpec) -> KMaterialValue:
    if spec.IsMultiple:
        if type(value) not in (tuple, list):
            raise ValueError("Material multiple-value property requires a sequence")
        return tuple(scalar_model(item, spec) for item in value)
    return scalar_model(value, spec)


def connection_model(row: Mapping[str, Any]) -> AssetLinks | None:
    if "connections" not in row:
        return None
    connection = row["connections"]
    if type(connection) is not dict or type(connection.get("present")) is not bool:
        raise ValueError("Material connection requires a boolean presence flag")
    if not connection["present"]:
        if set(connection) != {"present"}:
            raise ValueError("Absent material connections cannot carry target data")
        return None
    if set(connection) != {"present", "enabled", "assets"} or type(connection["assets"]) not in (tuple, list):
        raise ValueError("Present material connections require enabled and asset targets")
    return AssetLinks(connection["enabled"], tuple(connection["assets"]))


def property_models(rows: Sequence[Mapping[str, Any]], fields: tuple[PropertySpec, ...]) -> tuple[PropertyValue, ...]:
    indexed = {field.FieldName: field for field in fields}
    result = []
    for row in rows:
        name = row["name"]
        if name not in indexed:
            raise ValueError("Material property is absent from the supplied schema")
        result.append(PropertyValue(name, value_model(row["value"], indexed[name]), connection_model(row)))
    return tuple(result)


def material_models(materials: Sequence[Mapping[str, Any]], schemas: tuple[MaterialSchema, ...]) -> tuple[MaterialAsset, ...]:
    resolved = BuildSchemas(schemas)
    result = []
    for material in materials:
        name = material["schema"]
        if name not in resolved:
            raise ValueError("Material instance references an absent schema")
        fields = resolved[name]
        result.append(MaterialAsset(
            name,
            material["instance_id"],
            material["definition_id"],
            material["role"],
            property_models(material["definition_properties"], fields),
            property_models(material["properties"], fields),
        ))
    return tuple(result)


def encode_material_data(materials: Sequence[Mapping[str, Any]], schemas: Mapping[str, Element]) -> dict[str, bytes]:
    declared = schema_models(schemas)
    encoded = EncodeMaterials(material_models(materials, declared), declared)
    return {
        "DefinitionIteratorProperties.bin": encoded.DefinitionData,
        "InstanceProperties.bin": encoded.InstanceData,
        "AssetTableOfContents.bin": encoded.TableData,
    }


def decode_material_data(streams: Mapping[str, bytes], schemas: Mapping[str, Element]) -> tuple[MaterialAsset, ...]:
    material_data = MaterialData(
        streams["AssetTableOfContents.bin"],
        streams["DefinitionIteratorProperties.bin"],
        streams["InstanceProperties.bin"],
    )
    return DecodeMaterials(material_data, schema_models(schemas))


def reader_report(streams: Mapping[str, bytes], schemas: Mapping[str, Element]) -> dict[str, Any]:
    assets = decode_material_data(streams, schemas)
    return {
        "reader": "convert.formats.Fusion.MaterialCodec.DecodeMaterials",
        "scope": "Supplied Protein AssetData streams and explicit schema declarations; no package or native API access",
        "stream_sha256": {name: sha256(payload).hexdigest() for name, payload in streams.items()},
        "instances": len(assets),
        "instance_properties": sum(len(asset.Properties) for asset in assets),
        "definition_properties": sum(len(asset.Definitions) for asset in assets),
        "materials": [asdict(asset) for asset in assets],
    }
