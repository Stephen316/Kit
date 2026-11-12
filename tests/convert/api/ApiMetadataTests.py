from importlib.metadata import distribution as GetPackage
import re as RegexLib

import tomllib as TomlLib

from convert import convert as ConvertLegacy
from convert.api.ApiContext import KAdapterRegistry
from tests.convert.api.ApiTestPaths import KRootPath


# one sdk entry point prevents competing command surfaces from drifting apart
def CheckEntryPoint() -> None:
    EntryPoints = GetPackage("unicad-kit").entry_points
    assert [
        (ItemData.group, ItemData.name, ItemData.value) for ItemData in EntryPoints
    ] == [("kit", "convert", "convert:convert")]
    assert next(iter(EntryPoints)).load() is ConvertLegacy


def CheckMetadata() -> None:
    MetadataData = TomlLib.loads(
        (KRootPath / "pyproject.toml").read_text(encoding="utf-8")
    )
    ProjectData = MetadataData["project"]
    assert ProjectData["name"] == "unicad-kit"
    assert ProjectData["entry-points"] == {"kit": {"convert": "convert:convert"}}
    assert "scripts" not in ProjectData
    assert "gui-scripts" not in ProjectData
    assert ProjectData["license"] == "MIT"
    assert ProjectData["license-files"] == [
        "LICENSE",
        "src/convert/adapters/solidworks/container/OpenSwxLicense.md",
    ]
    assert {"Odin Glynn-Martin", "Stephen Harcourt"} <= {
        AuthorData["name"] for AuthorData in ProjectData["authors"]
    }
    assert ProjectData["urls"]["Repository"] == "https://github.com/TryUniCAD/Kit"
    assert MetadataData["tool"]["hatch"]["build"]["targets"]["sdist"]["include"] == [
        "/LICENSE",
        "/README.md",
        "/pyproject.toml",
        "/src",
        "/uv.lock",
    ]
    ReadmeText = (KRootPath / ProjectData["readme"]).read_text(encoding="utf-8")
    for SuffixText in (".SLDPRT", ".SLDASM", ".FCStd", ".CATPart", ".CATProduct"):
        assert SuffixText in ReadmeText


# readme guarantees remain tested because reversible defaults and strict mode define public behavior
def CheckReadme() -> None:
    ReadmeText = (KRootPath / "README.md").read_text(encoding="utf-8")
    assert "convert(source, destination)" in ReadmeText
    assert "allow_carrier=False" in ReadmeText
    assert "without requiring CAD software" in ReadmeText

    ReadmeSuffixes = {
        SuffixText.casefold()
        for RowText in ReadmeText.splitlines()
        if RowText.startswith("|")
        and RowText.split("|")[-2].strip() == "Reader and writer"
        for SuffixText in RegexLib.findall(r"`(\.[A-Za-z0-9]+)`", RowText)
    }
    ReaderSuffixes, WriterSuffixes = (
        {
            SuffixText.casefold()
            for AdapterData in AdapterSet
            for SuffixText in AdapterData.info.extensions
        }
        for AdapterSet in (KAdapterRegistry.readers(), KAdapterRegistry.writers())
    )
    assert ReadmeSuffixes == ReaderSuffixes & WriterSuffixes

    LicenseText = (KRootPath / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in LicenseText
    for AuthorName in ("Odin Glynn-Martin", "Stephen Harcourt"):
        assert AuthorName in ReadmeText
        assert AuthorName in LicenseText
