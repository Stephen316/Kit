KAuxHeaderSpec = "; ".join(
    (
        "Bytes AuxMarker 3; RS DwgVersion",
        "since AC1032 { RL MaintVersion } else { RS MaintVersion }",
        "RL SaveCount; RL MinusOne; RS SavesPartOne; RS SavesPartTwo; RL ReservedA",
        "RS SavedVersionA",
        "since AC1032 { RL SavedMaintA } else { RS SavedMaintA }",
        "RS SavedVersionB",
        "since AC1032 { RL SavedMaintB } else { RS SavedMaintB }",
        "RS CodeA; RS CodeB; RS CodeC; RS CodeD; RS CodeE; RS CodeF",
        "RL ReservedB; RL ReservedC; RL ReservedD; RL ReservedE; RL ReservedF",
        "RL TdCreateDay; RL TdCreateMsec; RL TdUpdateDay; RL TdUpdateMsec",
        "RL HandSeed; RL EduPlotStamp; RS ReservedShort; RS SavesDelta",
        "RL ReservedG; RL ReservedH; RL ReservedI; RL SaveCountAgain",
        "RL ReservedJ; RL ReservedK; RL ReservedL; RL ReservedM",
    )
)
KObjFreeSpaceSpec = "; ".join(
    (
        "RLL ReservedLong; RLL ApproxObjects; RL TdUpdateDay; RL TdUpdateMsec",
        "RC PairCount; each Pairs PairCount { RLL PairFirst; RLL PairSecond }",
    )
)
KAppHistorySpec = "; ".join(
    (
        "Bytes HistoryIds 32; RL LeadWord; WT InfoName; RL EntryCount",
        "each Entries EntryCount { Bytes EntryKey 16; WT EntryText }",
    )
)
KFileDepSpec = "; ".join(
    (
        "RL FeatureCount; each Features FeatureCount { ST FeatureName }",
        "RL FileCount; each Files FileCount { ST FullName; ST FoundPath",
        "ST FingerprintGuid; ST VersionGuid; RL FeatureIndex; RL TimeStamp",
        "RL FileSize; RS AffectsGraphics; RL RefCount }",
    )
)
KByteSpecs = {
    "AcDb:AuxHeader": KAuxHeaderSpec,
    "AcDb:Template": "WT Description; RS Measurement",
    "AcDb:ObjFreeSpace": KObjFreeSpaceSpec,
    "AcDb:RevHistory": "RL ReservedA; RL ReservedB; RL EntryCount; each Entries EntryCount { RL EntryValue }",
    "AcDb:AppInfoHistory": KAppHistorySpec,
    "AcDb:FileDepList": KFileDepSpec,
}
