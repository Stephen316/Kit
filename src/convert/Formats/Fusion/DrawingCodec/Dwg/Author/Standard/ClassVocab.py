# object base must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KObjectBase = "ObjectDBX Classes"

# model docs must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KModelDocs = "AcModelDocObj"

# synergy must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KSynergy = "AcSynergyObjDPW"

# object item must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KObjectItem = 499

# entity item must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KEntityItem = 498

# the class family shape must stay shared so drawing standard authoring uses one contract for compatible values
KClassFamily = tuple[str, int, int, int, int]

# the class names shape must stay shared so drawing standard authoring uses one contract for compatible values
KClassNames = tuple[tuple[str, str], ...]

# the object families order must stay explicit so native drawing objects use a consistent symbol vocabulary
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

# the view families order must stay explicit so native drawing objects use a consistent symbol vocabulary
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

# the assoc families order must stay explicit so native drawing objects use a consistent symbol vocabulary
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

# class families must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KClassFamilies = KObjectFamilies + KViewFamilies + KAssocFamilies
