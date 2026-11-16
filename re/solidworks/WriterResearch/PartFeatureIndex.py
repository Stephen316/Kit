# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the ordinary part's native feature index from typed save metadata."""

from dataclasses import dataclass

from PartFraming import VersionStorage
from PartManifests import EncodeXml

KFeaturesXml = "swXmlContents/Features"
KFeatureNs = "http://www.solidworks.com/sw2003/schema"
KDeclaration = '<?xml version="1.0" encoding="UTF-8"?>'
KConfiguration = "Default"


# both feature summaries use the same document identity and configuration
@dataclass(frozen=True)
class PartIndex:
    CreatedSeconds: int
    SavedPath: str
    ModelName: str
    LastModifiedStamp: int
    DocumentReference: str

    # reject incomplete save metadata before writing either summary member
    def __post_init__(self) -> None:
        if (
            type(self.CreatedSeconds) is not int
            or self.CreatedSeconds <= 0
            or type(self.LastModifiedStamp) is not int
            or self.LastModifiedStamp < 0
            or not all((self.SavedPath, self.ModelName, self.DocumentReference))
        ):
            raise ValueError("invalid ordinary part document identity")


# the root counts its file model and configuration objects and links their ids
def EncodeFeatures(Generation: int, Part: PartIndex) -> bytes:
    VersionStorage(Generation)
    FileId, ModelId, ConfigurationId = "3", "2", "1"
    SavedFile = (
        "swFile",
        {
            "id": FileId,
            "swDocType": "PART",
            "swCreationTime": str(Part.CreatedSeconds),
            "swPath": Part.SavedPath,
        },
        None,
    )
    Model = (
        "swModel",
        {
            "id": ModelId,
            "swName": Part.ModelName,
            "swConfigurationName": KConfiguration,
            "swConfigurationId": "0",
            "swLastModifiedStamp": str(Part.LastModifiedStamp),
            "swConfigurationFlags": "-2143288960",
            "swFileRef": FileId,
        },
        None,
    )
    Configuration = (
        "swConfiguration",
        {
            "id": ConfigurationId,
            "swName": KConfiguration,
            "swID": "0",
            "swReference": Part.DocumentReference,
            "swMostRecentConfiguration": "YES",
            "swConfigurationNeedsUpdate": "NO",
            "swDefeatureConfiguration": "NO",
            "swModelRef": ModelId,
        },
        None,
    )
    return EncodeXml(
        KDeclaration,
        "swSolidWorks",
        {"xmlns": KFeatureNs, "swObjCount": "3", "swVersion": str(Generation)},
        (
            ("swHeader", {"swObjCount": "1"}, (SavedFile,)),
            ("swModelList", {"swObjCount": "1"}, (Model,)),
            ("swConfigurationList", {"swObjCount": "1"}, (Configuration,)),
            ("swExtFeatureList", {"swObjCount": "0"}, None),
        ),
    )
