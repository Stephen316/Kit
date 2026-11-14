def point(x=0.0, y=0.0, z=0.0):
    return {'x': x, 'y': y, 'z': z}


def color(red=0.0, green=0.0, blue=0.0, alpha=1.0):
    return dict(red=red, green=green, blue=blue, alpha=alpha)


def defaults():
    return {
        'ManagedEntity': {'rParent': None},
        'ManagedGroup': {'children': []},
        'CommonBaseEntity': {'rClientObject': None},
        'CommonBaseGroupEntity': {'rClientObject': None},
        'CustomGroups': {'highWaterMark': 0},
        'BlobSerializerTrigger': {'partName': ''},
        'ManagedRootCollection': {'rootId': '', 'rooted': []},
        'ComponentsRoot': {'creationIndex': 0, 'externalCreationIndex': 0},
        'ComponentRootCollection': {},
        'ComponentInstancesRoot': {},
        'Overrides': {},
        'ComponentInstances': {},
        'ComponentBaseInstances': {'rACTInstances': None},
        'Bodies': dict(alterateBodies=False, creationIndex=0, groupChildren=[], isVisible=True, passiveIdGenerator=None, rBRepSerializer=None, selectable=True, surfaceGroups=None),
        'BRepHistorySerializer': {},
        'BRepSerializerBase': {'mapBodyId': [], 'rBodies': None, 'rBody': None},
        'BRepSerializer': {'topEntityPIDGenerator': None},
        'PassiveIdGenerator': {'addressOfTopEntities': [], 'nextId': 0, 'rBodies': None, 'rBody': None, 'scanOrderIndex': []},
        'Sketches': dict(groupChildren=[], highWaterMark=0, isVisible=True, selectable=True, sketchCustomGroups=None),
        'WorkGeometries': dict(groupChildren=[], highWaterMarkAxes=0, highWaterMarkPlanes=0, highWaterMarkPoints=0, highWaterMarkUCS=0, isVisible=True, selectable=True, workGeometryCustomGroups=None),
        'JointOrigins': {'highWaterMark': 0, 'visible': True},
        'AssyConstraints': {'constraintsHighWaterMark': 0, 'highWaterMark': 0, 'isVisible': True},
        'AssyConstraintOccurrences': {'highWaterMark': 0},
        'ContactSets': {'highWaterMark': 0, 'mode': 0},
        'MotionStudies': {'highWaterMark': 0},
        'SurfaceGroups': {'rUnstitchedGroup': None},
        'SelectionGroups': {'waterMark': 0},
        'WorkGeometryCustomGroups': {},
        'SketchCustomGroups': {},
        'ParameterTable': dict(bIsStateChangedByUser=False, expandedNodeSet=[], groupOrder=[], highWaterMark=0, rParameterSearchByNameHelper=None),
        'ParameterSearchByNameHelper': {'parameterMap': []},
        'DcNodes': {},
        'DcComputeManager': {'rOwnerFragment': None, 'sortIsCurrent': False, 'sortedNodesAll': []},
        'DcDependencyManager': {'mapsAreCurrent': False, 'predecessorMap': [], 'rOwnerFragment': None, 'successorMap': []},
        'DcAssociationManager': {'associationHolderMap': [], 'featureAssociationMap': [], 'rOwnerFragment': None},
        'DcFeatureIdManager': {'enetityIdMap': [], 'featureIdMap': [], 'obsoleteFeatureIds': [], 'rOwnerFragment': None},
        'DcXRefManager': {'new2XRefMap': [], 'rOwnerFragment': None},
        'DcComponent': {'bodiesVisibilityBeforeRollback': True, 'rFusionComponent': None},
        'DcComputeNode': {},
        'DcNode': dict(isActive=True, isEdited=False, isEliminated=False, rDynamicUpdateData=None, rGroupRepresentative=None, rParentFeature=None),
        'DynamicUpdateData': dict(bodies=[], isBodyOK=False, isPredecessorOK=False, predecessors=[], rOwnerNode=None, timeStamp=0, xRefPredecessorsHash=0),
        'DcCreationOrderFeatures': {'rFragment': None, 'representationFeatures': []},
        'Features': {'m_curFeatureId': 1},
        'OriginWorkGeometry': {'isVisible': False},
        'Relationships': {},
        'SubDSurfaceNodes': {},
        'Canvases': dict(canvasGroups=None, creationIndex=0, groupChildren=[], isVisible=True, m_bSelectable=True, m_opacity=1.0),
        'DcGroupFeatures': {'highWaterMark': 0},
        'DecalPatches': {'isVisible': True, 'm_opacity': 1.0},
        'PMIAnnotations': {'highWaterMarks': [], 'm_bVisible': True},
        'MeshBodies': {'creationIndex': 0, 'isSelectable': True, 'isVisible': True},
        'CanvasGroups': {},
        'LatticeRigDeformers': {'isSelectable': True, 'isVisible': True, 'm_latticeRigCreationIndex': 0},
        'EIPContexts': {'bVisible': True, 'creationIndex': 0},
        'EIPContext': dict(bActive=True, bLocalContext=True, bVisible=False, creationIndex=0, rBodies=None, rDerivedContextFeature=None, rSketches=None, rWorkGeometries=None, userName=''),
        'ComponentInstance': {},
        'HistoryFreeUpdateManager': {},
        'Arrangements': {'isVisible': True},
        'WorkGeometry': dict(actIdentifier='', groupParent=None, id=-1, isOrigin=True, originName='', rDcNode=None, rOwningDeriveFeature=None, selectable=True, userName=''),
        'Geometry3D': {'DAGNodeParents': []},
        'GeometryBase3D': {'isVisible': True, 'lineColor': color(), 'lineThickness': 1.0},
        'WorkPoint': {'point': point()},
        'WorkAxis': {'line': {'pointOnLine': point(), 'parametricDirection': point(1.0)}, 'lowerParam': 0.0, 'upperParam': 2.0},
        'WorkPlane': {'eCreationType': 0, 'llParam': {'x': -2.0, 'y': -2.0}, 'plane': {'normalReversed': False, 'origin': point(), 'uAxis': point(1.0), 'vAxis': point(0.0, 1.0)}, 'urParam': {'x': 2.0, 'y': 2.0}},
        'ThreadSettings': {'bModeledThread': False},
        'ProteinAssetManager': dict(PhysicalMaterialAssetReferences=[], PhysicalMaterialRefCountVector=[], VisualMaterialAssetReferences=[], VisualMaterialRefCountVector=[]),
        'AssetSettings': {},
        'UnitSystems': {},
        'NamedViews': {},
        'NamedLights': {'highWaterMark': 0, 'isSuppressed': False, 'isVisible': True},
        'PMISettings': dict(annotationSize=0.5, autoAnnotationSize=0.0, defaultLeadingZero=True, defaultPrecision=3, defaultTolerance=0.01, defaultTrailingZero=False, drawingStandard=0, generalNoteCustomSize=50.0, generalNoteSizeOption=1, inferDrawingStandard=True, useAutoAnnotationSize=True),
        'NamedTrackedEntitySet': {'trackedEntityByName': []},
        'WorkingModelPlaceholderRoot': {},
        'ComponentPostOffice': {'postOfficeDataVec': []},
        'OGSSerializer': {},
        'SceneSerializer': {},
        'MassPropertiesValue': {'areaOverride': -1.0, 'densityOverride': -1.0, 'massOverride': -1.0, 'volumeOverride': -1.0},
        'PhysicalMaterialValue': dict(ProteinAssetManager=None, assetReference='', libraryID='', name='', proteinMaterialID=''),
        'OccurrencePathValue': {},
        'ACTPassivePathValue': {'instanceIds': []},
    }


def settings():
    values = dict(ViewPortsDim=[], activeUnitSystem=None, assetSubType=2, bSceneUpBlank=False, curDisplayViewPorts='', currHomeExtentsHeight=20.0, currHomeExtentsWidth=20.0, currHomePos=point(20.0, -20.0, 20.0), currHomeProjection=1, currHomeTarget=point(), currHomeUp=point(0.0, 0.0, 1.0), currentProjection=1, defaultHomeExtentsHeight=20.0, defaultHomeExtentsWidth=20.0, defaultHomePos=point(20.0, -20.0, 20.0), defaultHomeProjection=1, defaultHomeTarget=point(), defaultHomeUp=point(0.0, 0.0, 1.0), defaultSceneFront=point(0.0, 1.0), defaultSceneUp=point(0.0, 0.0, 1.0), enableLayoutGridFadeAppearance=False, fitHome=True, globalBoundRadius=2.0, globalVisibilityOverride=[], groundPlaneOffset=0.0, layoutGridDimensionApp=0, lockGroundPlane=False, lockedGroundPlaneOffset=0.0, lockedGroundPlaneOrientation=point(0.0, 0.0, 1.0), locktoSelection=False, namedViews=None, perspWithOrthoFaces=False, pmiSettings=None, preferredEnvironment='', rNamedLights=None, renderSetting=None, sceneBoundBoxCenter=point(), sceneBoundBoxExtent=point(2.0, 2.0, 2.0), sceneBoundRadius=0.0, sceneFront=point(0.0, 1.0), sceneUp=point(0.0, 0.0, 1.0), settingsInitialized=True, threadSettings=None)
    return values


def numeric(name, millimeters, comment, birthday):
    return dict(UserDefaultUnit=False, actIdentifier='', birthday=birthday, booleanValue=False, comment=comment, creationIndex=1, dcParameter=None, expression=str(millimeters) + ' mm', expressionType=0, group=None, isDirty=False, isDriven=False, isExternal=False, isFavourite=False, isOrphan=False, isUserDefined=True, name='User Parameter', textValue='', unit='mm', userName=name, value=millimeters / 10.0)
