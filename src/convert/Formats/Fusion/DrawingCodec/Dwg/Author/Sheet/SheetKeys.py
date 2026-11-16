# named objects must remain consistent across callers so paper layouts retain consistent object ownership
KNamedObjects = "NOD"

# first sheet tab must remain consistent across callers so paper layouts retain consistent object ownership
KFirstSheetTab = 2

# block entries must remain consistent across callers so paper layouts retain consistent object ownership
KBlockEntries = "Control:BLOCK.Entries"

# paper space must remain consistent across callers so paper layouts retain consistent object ownership
KPaperSpace = "BLOCK_HEADER:*Paper_Space"

# model space must remain consistent across callers so paper layouts retain consistent object ownership
KModelSpace = "BLOCK_HEADER:*Model_Space"

# model owned must remain consistent across callers so paper layouts retain consistent object ownership
KModelOwned = KModelSpace + ".Owned"

# paper owned must remain consistent across callers so paper layouts retain consistent object ownership
KPaperOwned = KPaperSpace + ".Owned"

# layout folder must remain consistent across callers so paper layouts retain consistent object ownership
KLayoutFolder = "NOD/ACAD_LAYOUT"

# layout key must remain consistent across callers so paper layouts retain consistent object ownership
KLayoutKey = KLayoutFolder + "/Sheet"

# layout viewports must remain consistent across callers so paper layouts retain consistent object ownership
KLayoutViewports = KLayoutKey + ".Viewports"

# root folder needs a stable location so drawing sheet authoring resolves inputs independently of the caller working directory
KRootFolder = "NOD/SY_ROOT_DICTIONARY"

# paper folder must remain consistent across callers so paper layouts retain consistent object ownership
KPaperFolder = KPaperSpace + "/Xdic"

# paper networks must remain consistent across callers so paper layouts retain consistent object ownership
KPaperNetworks = KPaperFolder + "/ACAD_ASSOCNETWORK"

# paper network must remain consistent across callers so paper layouts retain consistent object ownership
KPaperNetwork = KPaperNetworks + "/ACAD_ASSOCNETWORK"

# network actions must remain consistent across callers so paper layouts retain consistent object ownership
KNetworkActions = KPaperNetwork + ".Actions"

# root networks needs a stable location so drawing sheet authoring resolves inputs independently of the caller working directory
KRootNetworks = "NOD/ACAD_ASSOCNETWORK"

# root network needs a stable location so drawing sheet authoring resolves inputs independently of the caller working directory
KRootNetwork = KRootNetworks + "/ACAD_ASSOCNETWORK"

# overall port must remain consistent across callers so paper layouts retain consistent object ownership
KOverallPort = KPaperSpace + "/Overall"

# scale key must remain consistent across callers so paper layouts retain consistent object ownership
KScaleKey = "NOD/ACAD_SCALELIST/B3"

# title block must remain consistent across callers so paper layouts retain consistent object ownership
KTitleBlock = "BLOCK_HEADER:ISO_TITLEBLOCK"

# source manager must remain consistent across callers so paper layouts retain consistent object ownership
KSourceManager = KRootFolder + "/SY_VIEWSOURCEMGR"

# fusion source must remain consistent across callers so paper layouts retain consistent object ownership
KFusionSource = KSourceManager + "/Xdic/ACAD_XREC_ROUNDTRIP/Source"
