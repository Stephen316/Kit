KObjectBase = "ObjectDBX Classes"
KModelDocs = "AcModelDocObj"
KSynergy = "AcSynergyObjDPW"
KObjectItem = 499
KEntityItem = 498
KClassFamily = tuple[str, int, int, int, int]
KClassNames = tuple[tuple[str, str], ...]
KObjectFamilies: tuple[tuple[KClassFamily, KClassNames], ...] = (
    (
        (KObjectBase, 0, KObjectItem, 22, 42),
        (
            ("ACDBDICTIONARYWDFLT", "AcDbDictionaryWithDefault"),
            ("ACDBPLACEHOLDER", "AcDbPlaceHolder"),
            ("LAYOUT", "AcDbLayout"),
        ),
    ),
    ((KObjectBase, 1153, KObjectItem, 23, 14), (("MATERIAL", "AcDbMaterial"),)),
    ((KObjectBase, 1153, KObjectItem, 27, 1), (("SCALE", "AcDbScale"),)),
)
KViewFamilies: tuple[tuple[KClassFamily, KClassNames], ...] = (
    (
        (KModelDocs, 129, KObjectItem, 33, 285),
        (
            ("ACDBVIEWREPSTANDARD", "AcDbViewRepStandard"),
            ("ACDBVIEWREP", "AcDbViewRep"),
            ("ACDBVIEWREPSOURCEMGR", "AcDbViewRepSourceMgr"),
            ("ACDBVIEWREPFUSIONSOURCE", "AcDbViewRepFusionSource"),
            ("ACDBVIEWREPORIENTATIONDEF", "AcDbViewRepOrientationDef"),
            ("ACDBVIEWREPORIENTATION", "AcDbViewRepOrientation"),
            ("ACDBSYNERGYMAPPINGS", "AcDbSynergyMappings"),
            ("ACDBREFERENCEDATA", "AcDbReferenceData"),
        ),
    ),
    (
        (KModelDocs, 0, KEntityItem, 33, 285),
        (
            ("ACDBVIEWREPBLOCKREFERENCE", "AcDbViewRepBlockReference"),
            ("DRAWINGVIEW", "AcDbViewBorder"),
        ),
    ),
)
KAssocFamilies: tuple[tuple[KClassFamily, KClassNames], ...] = (
    (
        (KObjectBase, 1025, KObjectItem, 27, 45),
        (
            ("ACDBASSOCNETWORK", "AcDbAssocNetwork"),
            ("ACDBASSOCACTION", "AcDbAssocAction"),
        ),
    ),
    (
        (KObjectBase, 1025, KObjectItem, 27, 50),
        (
            ("ACDBASSOCDEPENDENCY", "AcDbAssocDependency"),
            ("ACDBASSOCOBJECTACTIONPARAM", "AcDbAssocObjectActionParam"),
        ),
    ),
    (
        (KSynergy, 1025, KObjectItem, 33, 285),
        (
            ("ACDBASSOCVIEWREPACTIONBODY", "AcDbAssocViewRepActionBody"),
            ("ACDBASSOCVIEWBORDERACTIONPARAM", "AcDbAssocViewBorderActionParam"),
            ("ACDBASSOCVIEWREPACTIONPARAM", "AcDbAssocViewRepActionParam"),
        ),
    ),
    (
        (KSynergy, 1, KObjectItem, 33, 285),
        (("ACDBASSOCVIEWREPHATCHMANAGER", "AcDbAssocViewRepHatchManager"),),
    ),
)
KClassFamilies = KObjectFamilies + KViewFamilies + KAssocFamilies
