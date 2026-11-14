from typing import Literal
from uuid import UUID as UuidValue


def ConfigName(NameValue: str) -> Literal["table", "rule"]:
    Prefix = "DesignConfigurationTable.BlobParts/"
    for Label, Extension, KindValue in (
        ("DesignConfigurationTable", ".dsgcfg", "table"),
        ("DesignConfigurationRule", ".dsgcfgrule", "rule"),
    ):
        Start = Prefix + Label + "."
        if NameValue.startswith(Start) and NameValue.endswith(Extension):
            Identity = NameValue.removeprefix(Start).removesuffix(Extension)
            if str(UuidValue(Identity)) != Identity:
                raise ValueError("Configuration identity must be a canonical UUID")
            return "table" if KindValue == "table" else "rule"
    raise ValueError("Unsupported configuration part name")
