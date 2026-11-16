from importlib.metadata import distribution as GetPackage
import re as RegexLib

import tomllib as TomlLib

from convert import convert as ConvertLegacy
from convert.api.ApiContext import KAdapterRegistry
from KitCli.MainEntry import MainEntry
from tests.Convert.Api.ApiTestPaths import KRootPath


# installed command discovery must preserve the existing plugin entry point alongside the executable
def CheckEntryPoint() -> None:
    EntryPoints = GetPackage("unicad-kit").entry_points
    assert [
        (ItemData.group, ItemData.name, ItemData.value) for ItemData in EntryPoints
    ] == [
        ("console_scripts", "kit", "KitCli.MainEntry:MainEntry"),
        ("kit", "convert", "convert:convert"),
    ]
    assert (
        next(Value for Value in EntryPoints if Value.group == "kit").load()
        is ConvertLegacy
    )
    assert (
        next(Value for Value in EntryPoints if Value.group == "console_scripts").load()
        is MainEntry
    )


# the metadata contract needs boundary coverage so independent codecs retain consistent data contracts
def CheckMetadata() -> None:
    MetadataData = TomlLib.loads(
        (KRootPath / "pyproject.toml").read_text(encoding="utf-8")
    )
    ProjectData = MetadataData["project"]
    assert ProjectData["name"] == "unicad-kit"
    assert ProjectData["entry-points"] == {"kit": {"convert": "convert:convert"}}
    assert ProjectData["scripts"] == {"kit": "KitCli.MainEntry:MainEntry"}
    assert "gui-scripts" not in ProjectData
    assert ProjectData["license"] == "MIT"
    assert ProjectData["license-files"] == [
        "LICENSE",
        "src/convert/adapters/solidworks/Container/OpenSwxLicense.md",
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
        "/Cli",
        "/uv.lock",
    ]
    assert MetadataData["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/interchange",
        "src/convert",
        "Cli/KitCli",
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
