from dataclasses import replace as ReplaceData
from functools import cache as CacheValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.catia.Adapter import CatiaAdapter
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestPaths import KRootPath


@CacheValue
def ReadAssembly() -> CadDocument:
    NativePath = (
        KRootPath
        / "re/catia/examples/.CATProduct/Brake_Pedal_Assembly - Backup 1.CATProduct"
    )
    Document = CatiaAdapter().read(
        NativePath.read_bytes(), ReadOptions(include_brep=False)
    )
    assert Document.feature_timeline == ()
    assert Document.assembly is not None and Document.assembly.documents == ()
    assert Document.assembly.attributes["transform_status"] == "native-only"
    assert Document.assembly.attributes["constraint_status"] == "native-only"
    assert all(
        Instance.attributes["transform_resolved"] is False
        for Instance in Document.assembly.instances
    )
    return Document


def AssemblyCase(ModeValue: str, RelabelSource: bool) -> CadDocument:
    Document = ReadAssembly()
    Assembly = Document.assembly
    assert Assembly is not None
    if ModeValue == "status":
        Assembly = ReplaceData(
            Assembly,
            instances=tuple(
                ReplaceData(
                    Instance,
                    attributes={
                        NameText: Value
                        for NameText, Value in Instance.attributes.items()
                        if NameText != "transform_resolved"
                    },
                )
                for Instance in Assembly.instances
            ),
        )
    if ModeValue == "instance":
        Assembly = ReplaceData(
            Assembly,
            attributes={
                NameText: Value
                for NameText, Value in Assembly.attributes.items()
                if NameText not in {"transform_status", "constraint_status"}
            },
        )
    Source = (
        ReplaceData(Document.source, format_id="interchange.json")
        if RelabelSource
        else Document.source
    )
    return ReplaceData(Document, source=Source, assembly=Assembly)
