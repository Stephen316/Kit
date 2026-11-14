from math import pi as KHalfTurn

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue

KVarGroup = dict[str, KDraftValue]
KByLayerColor = 0xC0000000
KByBlockColor = 0xC1000000
KIndexColor = 0xC3000000
KDefaultWeight = 0xFFFE

KLegacyHead: KVarGroup = {
    "RequiredVersions": 0,
    "UnknownRealA": 412148564080.0,
    "UnknownRealB": 1.0,
    "UnknownRealC": 1.0,
    "UnknownRealD": 1.0,
    "UnknownTextA": "m",
    "UnknownTextB": "",
    "UnknownTextC": "",
    "UnknownTextD": "",
    "UnknownTextE": ".",
    "UnknownLongA": 0,
    "UnknownLongB": 0,
}

KSwitchVars: KVarGroup = {
    "DimAso": 1,
    "DimSho": 1,
    "PlineGen": 0,
    "OrthoMode": 0,
    "RegenMode": 1,
    "FillMode": 1,
    "QTextMode": 0,
    "PsLtScale": 1,
    "LimCheck": 0,
    "UnknownBitA": 0,
    "UsrTimer": 1,
    "SkPoly": 0,
    "AngDir": 0,
    "SplFrame": 0,
    "MirrText": 0,
    "WorldView": 1,
    "TileMode": 0,
    "PLimCheck": 0,
    "VisRetain": 1,
    "DispSilh": 0,
    "PEllipse": 0,
}

KCountVars: KVarGroup = {
    "ProxyGraphics": 1,
    "TreeDepth": 3020,
    "LUnits": 2,
    "LuPrec": 4,
    "AUnits": 0,
    "AuPrec": 0,
    "AttMode": 1,
    "PdMode": 0,
    "UnknownLongC": 0x30303030,
    "UnknownLongD": 0x1D050900,
    "UnknownLongE": 0x4D353930,
}

KSurfaceVars: KVarGroup = {
    "UserIOne": 0,
    "UserITwo": 0,
    "UserIThree": 0,
    "UserIFour": 0,
    "UserIFive": 0,
    "SplineSegs": 8,
    "SurfU": 6,
    "SurfV": 6,
    "SurfType": 6,
    "SurfTabOne": 6,
    "SurfTabTwo": 6,
    "SplineType": 6,
    "ShadEdge": 3,
    "ShadeDif": 70,
    "UnitMode": 0,
    "MaxActVp": 64,
    "IsoLines": 4,
    "CmlJust": 0,
    "TextQlty": 50,
}

KRealVars: KVarGroup = {
    "TraceWid": 1.0,
    "SketchInc": 1.0,
    "FilletRad": 0.0,
    "Thickness": 0.0,
    "AngBase": 0.0,
    "PdSize": 0.0,
    "PlineWid": 0.0,
    "UserROne": 0.0,
    "UserRTwo": 0.0,
    "UserRThree": 0.0,
    "UserRFour": 0.0,
    "UserRFive": 0.0,
    "ChamferA": 0.0,
    "ChamferB": 0.0,
    "ChamferC": 0.0,
    "ChamferD": 0.0,
    "FacetRes": 0.5,
    "CmlScale": 20.0,
    "CeltScale": 1.0,
}

KStampVars: KVarGroup = {
    "TdCreateDay": 0,
    "TdCreateMsec": 0,
    "TdUpdateDay": 0,
    "TdUpdateMsec": 0,
    "UnknownLongF": 0x4D303030,
    "UnknownLongG": 0x1D000000,
    "UnknownLongH": 0x30303030,
    "TdInDwgDay": 0,
    "TdInDwgMsec": 0,
    "TdUsrTimerDay": 0,
    "TdUsrTimerMsec": 0,
    "CeColorIndex": 0,
    "CeColorRgb": KByLayerColor,
    "CeColorFlags": 0,
}

KModernVars: KVarGroup = {
    "CameraDisplay": 0,
    "UnknownLongI": 0,
    "UnknownLongJ": 10,
    "UnknownRealE": 1.0,
    "StepsPerSec": 2.0,
    "StepSize": 6.0,
    "ThreeDDwfPrec": 2.0,
    "LensLength": 50.0,
    "CameraHeight": 0.0,
    "SolidHist": 0,
    "ShowHist": 1,
    "PSolWidth": 5.0,
    "PSolHeight": 80.0,
    "LoftAngOne": KHalfTurn / 2,
    "LoftAngTwo": KHalfTurn / 2,
    "LoftMagOne": 0.0,
    "LoftMagTwo": 0.0,
    "LoftParam": 7,
    "LoftNormals": 1,
    "Latitude": 37.795,
    "Longitude": -122.394,
    "NorthDirection": 0.0,
    "TimeZone": 0,
    "LightGlyphDisplay": 1,
    "TileModeLightSynch": 1,
    "DwfFrame": 2,
    "DgnFrame": 0,
    "UnknownBitB": 1,
}

KInterfereVars: KVarGroup = {
    "InterfereColorIndex": 0,
    "InterfereColorRgb": KIndexColor | 1,
    "InterfereColorFlags": 0,
}
