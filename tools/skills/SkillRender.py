# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from tools.skills.Descriptions import KDescriptions
from tools.skills.SkillMetadata import KSkillMetadata
from tools.skills.SkillPaths import KRootPath, GetSourcePath
from tools.skills.SkillSource import StripSource
from tools.skills.YamlScalar import QuoteYaml

# shared license identity keeps every generated skill compatible with agent discovery
KLicenseName = "MIT"


# single skill rendering guarantees checks compare the exact bytes writers produce
def RenderSkill(SkillName: str) -> str:
    SourceFile = GetSourcePath(SkillName)
    MetadataInfo = {
        "source": SourceFile.relative_to(KRootPath).as_posix(),
        "kiro-inclusion": "always",
        **KSkillMetadata.get(SkillName, {}),
    }
    FrontMatter = [
        "---",
        f"name: {SkillName}",
        f"description: {QuoteYaml(KDescriptions[SkillName])}",
        f"license: {KLicenseName}",
        "metadata:",
        *(
            f"  {KeyName}: {QuoteYaml(ValueText)}"
            for KeyName, ValueText in MetadataInfo.items()
        ),
        "---",
        "",
        "",
    ]
    SourceText = SourceFile.read_text(encoding="utf-8")
    return "\n".join(FrontMatter) + StripSource(SourceText)
