from convert import open_document as OpenDocument
from tests.convert.api.ApiTestPaths import KRootPath


def TestInchDia() -> None:
    SourcePath = (
        KRootPath
        / "re"
        / "automation"
        / "PairedCaptures"
        / "P02"
        / "solidworks-4a9e35f34a39"
        / "P02-solidworks-units-inch.SLDPRT"
    )
    Document = OpenDocument(SourcePath)
    (Diameter,) = (
        Parameter
        for Parameter in Document.parameters
        if Parameter.name == "diameter_mm"
    )
    assert Diameter.attributes["source_text"] == "<MOD-DIAM>0.39"
    assert Diameter.attributes["native_value"] == 0.01
    assert Diameter.value.value == 10.0
    assert Diameter.value.unit == "mm"
