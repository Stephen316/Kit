# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import ast as AstLib
from pathlib import Path as FilePath

from convert.adapters import AdapterRegistry
from tests.convert.api.ApiTestHelpers import ListApiTrees, ListFormatPacks
from tests.convert.api.ApiTestPaths import KRootPath


# payload constructors must declare semantics explicitly because inference would make extraction lossy
def CheckPayloadArg() -> None:
    ConstructorCalls: list[tuple[FilePath, AstLib.Call]] = []
    for SourcePath in (KRootPath / "src").rglob("*.py"):
        SyntaxTree = AstLib.parse(
            SourcePath.read_text(encoding="utf-8"),
            filename=str(SourcePath),
        )
        for NodeData in AstLib.walk(SyntaxTree):
            if not isinstance(NodeData, AstLib.Call):
                continue
            IsConstructor = (
                isinstance(NodeData.func, AstLib.Name)
                and NodeData.func.id == "BrepPayload"
                or isinstance(NodeData.func, AstLib.Attribute)
                and NodeData.func.attr == "BrepPayload"
            )
            if IsConstructor:
                ConstructorCalls.append((SourcePath, NodeData))
    assert ConstructorCalls
    for SourcePath, ConstructorData in ConstructorCalls:
        KeywordNames = {KeywordData.arg for KeywordData in ConstructorData.keywords}
        assert {
            "role",
            "file_extension",
        } <= KeywordNames, f"{SourcePath}:{ConstructorData.lineno} must declare payload role and extension"


# public composition must stay format neutral so adding adapters never edits api orchestration
def CheckNoFormats() -> None:
    PackageNames = ListFormatPacks()
    RegistryData = AdapterRegistry()
    _ = RegistryData.introspect()
    AdapterNames = {
        type(AdapterData).__name__
        for AdapterData in (*RegistryData.readers(), *RegistryData.writers())
    }
    FormatNames = {NameText.rsplit(".", 1)[-1] for NameText in PackageNames}
    for SourcePath, SyntaxTree in ListApiTrees(KRootPath):
        for NodeData in AstLib.walk(SyntaxTree):
            if isinstance(NodeData, AstLib.Import):
                assert not any(
                    AliasData.name == PackageName
                    or AliasData.name.startswith(PackageName + ".")
                    for AliasData in NodeData.names
                    for PackageName in PackageNames
                ), SourcePath
            if isinstance(NodeData, AstLib.ImportFrom):
                ModuleName = NodeData.module or ""
                assert not any(
                    ModuleName == PackageName
                    or ModuleName == PackageName.removeprefix("convert.")
                    or ModuleName.startswith(PackageName + ".")
                    or ModuleName.startswith(PackageName.removeprefix("convert.") + ".")
                    for PackageName in PackageNames
                ), SourcePath
                if ModuleName in {"adapters", "convert.adapters"}:
                    ImportedNames = {AliasData.name for AliasData in NodeData.names}
                    assert not (AdapterNames | FormatNames) & ImportedNames
