# root versions needs a stable location so document reconstruction resolves inputs independently of the caller working directory
KRootVersions = (
    ("Application", 1),
    ("CAM", 4),
    ("ParaMesh", 8),
    ("SimCommon", 30005),
    ("SimFEACSObjects", 2),
    ("SimFluidDynamics", 2),
    ("SimStructuralAttributes", 10002),
)

# the asset versions order must stay explicit so model state retains its native feature and ownership relationships
KAssetVersions = (
    ("Application", 139),
    ("ParaMesh", 13),
    ("Server", 36),
    ("VolField", 4),
)

# the software version variants need one shared contract so document reconstruction cannot omit a supported value shape
KSoftwareVersion = (2706 << 50) | (1 << 38) | 17
