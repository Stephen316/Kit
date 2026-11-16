from dataclasses import replace as ReplaceData

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import (
    AssemblyData,
    CadDocument,
    ComponentDoc,
)


# an embedded marked component exercises the recursive guard without changing outer evidence
def NestedDocument(Original: CadDocument, Marked: CadDocument) -> CadDocument:
    Nested = ReplaceData(
        Original,
        assembly=AssemblyData(
            "definition:root",
            (
                ComponentDef("definition:root", "Root", ComponentKind.KAssembly),
                ComponentDef(
                    "definition:part",
                    "Part",
                    (
                        ComponentKind.KAssembly
                        if Marked.assembly is not None
                        else ComponentKind.KPart
                    ),
                    document_id="document:part",
                ),
            ),
            (
                ComponentInst(
                    "instance:part", "Part", "definition:part", "definition:root"
                ),
            ),
            documents=(ComponentDoc("document:part", Marked),),
        ),
    )
    return ReplaceData(Nested, capabilities=Nested.capabilities | InferCaps(Nested))
