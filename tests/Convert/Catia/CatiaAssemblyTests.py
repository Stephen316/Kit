from __future__ import annotations as Annotations

from dataclasses import replace as Replace
import io as IoStream
from pathlib import Path as FilePath
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile

import pytest as Pytest

from convert import (
    ApplicationUsabilityError as AppUsabilityError,
    convert as Convert,
    open_document as OpenDoc,
)
from convert.adapters import ReadOptions
from convert.adapters.catia.Adapter import CatiaAdapter, WriteCatia
from convert.adapters.catia.Assembly import (
    DecodeProductA as DecodeProductTable,
    IsUnderRoot as UnderRoot,
    NativeProductE as NativeProductAsm,
)
from convert.adapters.catia.Container import BuildCfvTwo, CfvTwoArchive
from convert.adapters.freecad import (
    read_freecad as ReadFreecad,
    write_freecad as WriteFreecad,
)
from convert.adapters.freecad.Adapter import FreeCadAdapter
from interchange import (
    ComponentKind,
    Matrix4 as MatrixFour,
    frozen_mapping as FrozenMapping,
)
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.NativeWrites.IsNativeBlock import IsNativeBlock
from tests.Convert.Catia.MetadataAccess import GetObjectRows, GetString

# this binding exists because shared behavior needs one stable value
KRootValue = FilePath(__file__).parents[3]

# this binding exists because shared behavior needs one stable value
KCatproducts = KRootValue / "re" / "catia" / "examples" / ".CATProduct"


# this definition exists because focused behavior needs one stable owner
def ProductStream(Tokens: tuple[tuple[str, str], ...]) -> bytes:
    Values: list[bytes] = []
    for Value, Encoding in Tokens:
        RawValue = Value.encode(Encoding)
        if len(RawValue) > 254:
            raise ValueError("test product token exceeds the one-byte length field")
        Values.append(bytes((len(RawValue) + 1,)) + RawValue)
    return b"".join(Values)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("NameValue", "RootName", "TokenCount", "InstanceCount"),
    (
        ("Brake_Pedal_Assembly - Backup 1.CATProduct", "Brake_Pedal_Assembly", 100, 48),
        ("Brake_Pedal_Assembly - Backup 2.CATProduct", "Brake_Pedal_Assembly", 37, 7),
        ("Tilton_Set.CATProduct", "Tilton", 38, 4),
    ),
)
def TestEveryLength(
    NameValue: str, RootName: str, TokenCount: int, InstanceCount: int
) -> None:
    PathValue = KCatproducts / NameValue
    Table = DecodeProductTable(CfvTwoArchive.from_bytes(PathValue.read_bytes()))
    assert Table.root_name == RootName
    assert Table.stream_name == "Data"
    assert len(Table.tokens) == TokenCount
    assert len(Table.occurrences) == InstanceCount


# this definition exists because focused behavior needs one stable owner
def TestCatproductE() -> None:
    Brake = DecodeProductTable(
        CfvTwoArchive.from_bytes(
            (KCatproducts / "Brake_Pedal_Assembly - Backup 1.CATProduct").read_bytes()
        )
    )
    assert (
        Brake.occurrences[-1].definition_name,
        Brake.occurrences[-1].instance_name,
    ) == ("Low_Head_M4x20 1", "Low_Head_M4x20 2")
    assert (
        sum(
            (
                ItemValue.definition_name == "Washer_6_DIN_433_1"
                for ItemValue in Brake.occurrences
            )
        )
        == 4
    )
    Tilton = DecodeProductTable(
        CfvTwoArchive.from_bytes((KCatproducts / "Tilton_Set.CATProduct").read_bytes())
    )
    assert [
        (ItemValue.definition_name, ItemValue.instance_name)
        for ItemValue in Tilton.occurrences
    ] == [
        ("4876", "I_4876.2"),
        ("4876_1", "I_4876.3"),
        ("4784", "I_4784.5"),
        ("Brake_bias_90_degree_coupler", "I_Brake_bias_90_degree_coupler.1"),
    ]


# this definition exists because focused behavior needs one stable owner
def TestCatproductI() -> None:
    DataValue = BuildCfvTwo(
        (
            (
                "Data",
                ProductStream(
                    (
                        ("ASMPRODUCT", "utf-8"),
                        ("RootA", "utf-8"),
                        ("_Reps", "utf-8"),
                        ("PartA", "utf-8"),
                        ("_InstanceName", "utf-8"),
                        ("Instance A", "utf-8"),
                        ("IsRoot", "utf-8"),
                    )
                ),
            ),
            (
                "OtherProductTable",
                ProductStream(
                    (
                        ("ASMPRODUCT", "utf-8"),
                        ("RootB", "utf-8"),
                        ("_Reps", "utf-8"),
                        ("PartB", "utf-8"),
                        ("_InstanceName", "utf-8"),
                        ("Instance B", "utf-8"),
                        ("IsRoot", "utf-8"),
                    )
                ),
            ),
        )
    )
    Table = DecodeProductTable(CfvTwoArchive.from_bytes(DataValue))
    assert Table.root_name == "RootA"
    assert [ItemValue.root_name for ItemValue in Table.alternatives] == ["RootB"]
    DocValue = CatiaAdapter().read(DataValue, ReadOptions(include_brep=False))
    assert DocValue.assembly is not None
    assert [
        ItemValue["root_name"]
        for ItemValue in GetObjectRows(
            DocValue.assembly.attributes["native_table_candidates"]
        )
    ] == ["RootA", "RootB"]
    assert "catia.product.root_ambiguous" in {
        ItemValue.code for ItemValue in DocValue.diagnostics
    }


# this definition exists because focused behavior needs one stable owner
def TestCatproductG(TmpPath: FilePath) -> None:
    Source = KRootValue / "re" / "catia" / "examples" / ".CATPart" / "4876.CATPart"
    Renamed = TmpPath / "unrelated-name.CATPart"
    _ = Renamed.write_bytes(Source.read_bytes())
    DocValue = CatiaAdapter().read(
        KCatproducts / "Tilton_Set.CATProduct",
        ReadOptions(
            include_brep=False, values=FrozenMapping({"component_search_root": TmpPath})
        ),
    )
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    Definition = next(
        (ItemValue for ItemValue in AsmValue.definitions if ItemValue.name == "4876")
    )
    assert FilePath(Definition.source_path) == Renamed.resolve()
    assert Definition.document_id


# this definition exists because focused behavior needs one stable owner
def TestCatproductJ(TmpPath: FilePath) -> None:
    Source = KRootValue / "re" / "catia" / "examples" / ".CATPart" / "4876.CATPart"
    First = TmpPath / "a.CATPart"
    Second = TmpPath / "b.CATPart"
    _ = First.write_bytes(Source.read_bytes())
    _ = Second.write_bytes(Source.read_bytes())
    DocValue = CatiaAdapter().read(
        KCatproducts / "Tilton_Set.CATProduct",
        ReadOptions(
            include_brep=False, values=FrozenMapping({"component_search_root": TmpPath})
        ),
    )
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    Definition = next(
        (ItemValue for ItemValue in AsmValue.definitions if ItemValue.name == "4876")
    )
    assert Definition.source_path == ""
    assert Definition.document_id == ""
    assert {
        FilePath(GetString(ItemValue["path"])).name
        for ItemValue in GetObjectRows(
            Definition.attributes["native_reference_candidates"]
        )
    } == {"a.CATPart", "b.CATPart"}
    DiagValue = next(
        (
            ItemValue
            for ItemValue in DocValue.diagnostics
            if ItemValue.code == "catia.product.component_source_ambiguous"
        )
    )
    assert DiagValue.attributes["definition_name"] == "4876"


# this definition exists because focused behavior needs one stable owner
def TestCatproductH() -> None:
    PathValue = KCatproducts / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    DocValue = CatiaAdapter().read(PathValue, ReadOptions(include_brep=False))
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    assert len(AsmValue.instances) == 48
    assert len(AsmValue.definitions) == 25
    assert len(AsmValue.documents) == 19
    Definitions = {ItemValue.name: ItemValue for ItemValue in AsmValue.definitions}
    assert FilePath(Definitions["Brake_pedal"].source_path).name == "Pedal_Body.CATPart"
    assert Definitions["Brake_pedal"].kind == ComponentKind.PART
    assert (
        FilePath(Definitions["Screw_ISO_7379_M6_8_30"].source_path).name
        == "Fitted_Bolet_M6_8x30.CATPart"
    )
    assert (
        FilePath(Definitions["Low_Head_M4x20 1"].source_path).name
        == "Low_Head_M4x20.CATPart"
    )
    Tilton = Definitions["Tilton"]
    assert Tilton.kind == ComponentKind.ASSEMBLY
    assert FilePath(Tilton.source_path).name == "Tilton_Set.CATProduct"
    Linked = AsmValue.document(Tilton.document_id)
    assert Linked.assembly is not None
    LinkedDefinitions = {
        ItemValue.name: ItemValue for ItemValue in Linked.assembly.definitions
    }
    assert FilePath(LinkedDefinitions["4876_1"].source_path).name == "4876_1.CATPart"
    assert LinkedDefinitions["4876_1"].document_id
    assert AsmValue.attributes["linked_document_count"] == 19
    assert AsmValue.attributes["linked_feature_count"] == 18
    Missing = next(
        (
            ItemValue
            for ItemValue in DocValue.diagnostics
            if ItemValue.code == "catia.product.component_sources_missing"
        )
    )
    assert Missing.attributes["definition_names"] == (
        "Brake_Platform_2",
        "Brake_Platform",
        "Brake_Pedal_Shaft",
        "Reservoir_Holder",
        "Foot_Plate",
    )


# this definition exists because focused behavior needs one stable owner
def TestCatproductF() -> None:
    PathValue = KCatproducts / "Tilton_Set.CATProduct"
    DataValue = PathValue.read_bytes()
    DocValue = CatiaAdapter().read(PathValue, ReadOptions(include_brep=False))
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    for Instance in AsmValue.instances:
        Provenance = Instance.provenance
        assert Provenance is not None
        Encoded = b"".join(
            (
                DataValue[SpanValue.offset : SpanValue.offset + SpanValue.length]
                for SpanValue in Provenance.spans
            )
        )
        assert Encoded == Instance.name.encode("ascii")
        assert all((SpanValue.stream == "Data" for SpanValue in Provenance.spans))
    RootValue = AsmValue.definition(AsmValue.root_definition_id)
    Provenance = RootValue.provenance
    assert Provenance is not None
    Encoded = b"".join(
        (
            DataValue[SpanValue.offset : SpanValue.offset + SpanValue.length]
            for SpanValue in Provenance.spans
        )
    )
    assert Encoded == b"Tilton"


# this definition exists because focused behavior needs one stable owner
def TestCatproductP() -> None:
    DocValue = CatiaAdapter().read(
        KCatproducts / "Tilton_Set.CATProduct", ReadOptions(include_brep=False)
    )
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    assert AsmValue.mates == ()
    assert all(
        (ItemValue.transform == MatrixFour() for ItemValue in AsmValue.instances)
    )
    assert all(
        (
            ItemValue.attributes["transform_resolved"] is False
            for ItemValue in AsmValue.instances
        )
    )
    assert AsmValue.attributes["transform_status"] == "native-only"
    assert AsmValue.attributes["constraint_status"] == "native-only"
    assert {ItemValue.code for ItemValue in DocValue.diagnostics} >= {
        "catia.product.transforms_unresolved",
        "catia.product.constraints_unresolved",
    }


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "NameValue",
    (
        "Brake_Pedal_Assembly - Backup 1.CATProduct",
        "Brake_Pedal_Assembly - Backup 2.CATProduct",
        "Tilton_Set.CATProduct",
    ),
)
def TestEveryByte(NameValue: str, TmpPath: FilePath) -> None:
    Source = KCatproducts / NameValue
    DocValue = CatiaAdapter().read(Source)
    assert IsNativeBlock(DocValue, CatiaAdapter().write, ".CATProduct")


# this definition exists because focused behavior needs one stable owner
def TestChangedBase(TmpPath: FilePath) -> None:
    Source = KCatproducts / "Tilton_Set.CATProduct"
    DocValue = CatiaAdapter().read(Source)
    assert DocValue.assembly is not None
    ChangedAsm = Replace(
        DocValue.assembly,
        attributes=FrozenMapping(
            {**DocValue.assembly.attributes, "user.edit": "changed"}
        ),
    )
    Changed = Replace(DocValue, assembly=ChangedAsm)
    assert IsNativeBlock(Changed, CatiaAdapter().write, ".CATProduct")


# this definition exists because focused behavior needs one stable owner
def TestCatproductD() -> None:
    Source = KCatproducts / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    DocValue = CatiaAdapter().read(Source.read_bytes(), ReadOptions(include_brep=False))
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    assert len(AsmValue.instances) == 48
    assert AsmValue.documents == ()


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Values", "Limit"),
    (
        ({"component_search_max_files": 1}, "files"),
        ({"component_search_max_total_bytes": 1}, "total_bytes"),
        (
            {
                "component_search_root": KRootValue / "re" / "catia" / "examples",
                "component_search_max_depth": 0,
            },
            "depth",
        ),
    ),
)
def TestCatproductB(Values: dict[str, object], Limit: str) -> None:
    DocValue = CatiaAdapter().read(
        KCatproducts / "Tilton_Set.CATProduct",
        ReadOptions(include_brep=False, strict=False, values=FrozenMapping(Values)),
    )
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    assert AsmValue.documents == ()
    DiagValue = next(
        (
            ItemValue
            for ItemValue in DocValue.diagnostics
            if ItemValue.code == "catia.product.component_search_limit"
        )
    )
    assert DiagValue.attributes["limit"] == Limit


# this definition exists because focused behavior needs one stable owner
def TestCatproductC(TmpPath: FilePath) -> None:
    LinkValue = TmpPath / "outside-parts"
    try:
        LinkValue.symlink_to(
            KRootValue / "re" / "catia" / "examples" / ".CATPart",
            target_is_directory=True,
        )
    except OSError:
        Pytest.skip("directory symlinks are unavailable")
    DocValue = CatiaAdapter().read(
        KCatproducts / "Tilton_Set.CATProduct",
        ReadOptions(
            include_brep=False,
            strict=False,
            values=FrozenMapping({"component_search_root": TmpPath}),
        ),
    )
    AsmValue = DocValue.assembly
    assert AsmValue is not None
    assert AsmValue.documents == ()
    Rejected = tuple(
        (
            ItemValue
            for ItemValue in DocValue.diagnostics
            if ItemValue.code == "catia.product.component_search_rejected"
        )
    )
    assert any(
        (ItemValue.attributes["reason"] == "reparse_point" for ItemValue in Rejected)
    )


# this definition exists because focused behavior needs one stable owner
def TestCatproduct() -> None:
    PathValue = KCatproducts / "Tilton_Set.CATProduct"
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Adapter = CatiaAdapter()

    # this definition exists because focused behavior needs one stable owner
    def Mismatched(Component: FilePath, Options: ReadOptions) -> CadDocument:
        Values = dict(Options.values)
        Values["resolve_components"] = False
        DocValue = Adapter.read(
            Component,
            Replace(
                Options,
                strict=False,
                values=FrozenMapping(Values),
            ),
        )
        return Replace(DocValue, source=Replace(DocValue.source, sha256="0" * 64))

    AsmValue, Diagnostics = NativeProductAsm(
        Archive,
        str(PathValue.resolve()),
        ReadOptions(include_brep=False, strict=False),
        Mismatched,
    )
    assert AsmValue.documents == ()
    Changed = tuple(
        (
            ItemValue
            for ItemValue in Diagnostics
            if ItemValue.code == "catia.product.component_source_changed"
        )
    )
    assert len(Changed) == 4
    assert all(
        (ItemValue.attributes["indexed_sha256"] != "0" * 64 for ItemValue in Changed)
    )


# this definition exists because focused behavior needs one stable owner
def TestCatproductO(TmpPath: FilePath) -> None:
    Source = KCatproducts / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    Original = OpenDoc(Source)
    AsmValue = Original.assembly
    assert AsmValue is not None
    assert len(AsmValue.instances) == 48
    assert len(AsmValue.definitions) == 25
    assert len(AsmValue.documents) == 19
    assert AsmValue.mates == ()
    assert IsNativeBlock(Original, FreeCadAdapter().write, ".FCStd")


# this definition exists because focused behavior needs one stable owner
def TestCatproductN() -> None:
    Source = KCatproducts / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    DocValue = OpenDoc(Source)
    assert IsNativeBlock(DocValue, FreeCadAdapter().write, ".FCStd")


# this binding exists because shared behavior needs one stable value
globals()["ApplicationUsabilityError"] = AppUsabilityError

# this binding exists because shared behavior needs one stable value
globals()["CATPRODUCTS"] = KCatproducts

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Archive"] = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["Matrix4"] = MatrixFour

# this binding exists because shared behavior needs one stable value
globals()["Path"] = FilePath

# this binding exists because shared behavior needs one stable value
globals()["ROOT"] = KRootValue


# this binding exists because shared behavior needs one stable value
globals()["_product_stream"] = ProductStream

# this binding exists because shared behavior needs one stable value
globals()["_under_root"] = UnderRoot

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["build_cfv2"] = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
globals()["convert"] = Convert

# this binding exists because shared behavior needs one stable value
globals()["decode_product_table"] = DecodeProductTable

# this binding exists because shared behavior needs one stable value
globals()["frozen_mapping"] = FrozenMapping

# this binding exists because shared behavior needs one stable value
globals()["io"] = IoStream

# this binding exists because shared behavior needs one stable value
globals()["native_product_assembly"] = NativeProductAsm

# this binding exists because shared behavior needs one stable value
globals()["open_document"] = OpenDoc

# this binding exists because shared behavior needs one stable value
globals()["pytest"] = Pytest

# this binding exists because shared behavior needs one stable value
globals()["read_freecad"] = ReadFreecad

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["write_catia"] = WriteCatia

# this binding exists because shared behavior needs one stable value
globals()["write_freecad"] = WriteFreecad

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile
