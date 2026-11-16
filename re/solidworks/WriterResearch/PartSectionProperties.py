# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write the empty native custom and configuration property sections."""

from PartManifests import EncodeXml, KOffice
from PartSimpleProperties import KDecl, KVTypes

KCustomXml = "docProps/custom.xml"
KConfigXml = "docProps/Config-0-Properties.xml"
KConfigNs = "http://www.solidworks.com/config-properties"
KDocSummary = "{D5CDD502-2E9C-101B-9397-08002B2CF9AE}"
KUserProps = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"
KUtf8 = 65001


# the two empty sections have typed property values even with an empty name dictionary
def PropertyNode(Pid: int, ValueName: str, Value: str):
    return (
        "property",
        {"name": "", "pid": str(Pid), "TypeID": "0"},
        ((f"vt:{ValueName}", {}, Value),),
    )


# the empty dictionary is retained in both the document and configuration scopes
def SectionNode(Name: str, FormatId: str, Nodes):
    Dictionary = ("propertyNameDictionaryElement", {"name": "", "pid": "0"}, None)
    return (
        "propertySection",
        {"xmlns": "", "name": Name, "fmtid": FormatId},
        (*Nodes, Dictionary),
    )


# ordinary empty scopes differ only in their document-level summary values
def EncodeSectionProps(SummaryFlag: bool) -> dict[str, bytes]:
    if SummaryFlag is not False:
        raise ValueError(
            "ordinary empty property sections require the observed summary flag No"
        )
    CodePage = PropertyNode(1, "i2", str(KUtf8))
    User = SectionNode("UserDefinedProperties", KUserProps, (CodePage,))
    Summary = SectionNode(
        "DocumentSummaryInformation",
        KDocSummary,
        (CodePage, PropertyNode(22, "bool", "No")),
    )
    EmptySummary = SectionNode("DocumentSummaryInformation", KDocSummary, ())
    return {
        KCustomXml: EncodeXml(
            KDecl,
            "Properties",
            {"xmlns": KOffice + "/custom-properties", "xmlns:vt": KVTypes},
            (Summary, User),
            ShortEmpty=False,
        ),
        KConfigXml: EncodeXml(
            KDecl,
            "ConfigProperties",
            {"xmlns": KConfigNs, "xmlns:vt": KVTypes},
            (EmptySummary, User),
            ShortEmpty=False,
        ),
    }
