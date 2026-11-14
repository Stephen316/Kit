from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'src/convert/formats/Fusion/GraphicsCodec'
PREFIX = 'convert.formats.Fusion.GraphicsCodec.Model.'
MODELS = {
 'Values/ObjectRef': ('', 'ClassName: str\nObjectId: str'),
 'Values/EntityRef': ('', 'SegmentId: int\nObjectId: int'),
 'Values/VertexField': ('', 'TypeCode: int\nUsageCode: int\nWordOffset: int\nStreamIndex: int\nUsageIndex: int\nInstanceMode: int'),
 'Values/VertexFormat': ('Values.VertexField', 'Fields: tuple[VertexField, ...]'),
 'Values/VertexData': ('Values.ObjectRef', 'DynamicFlag: bool\nFormatRef: ObjectRef\nStreamIndex: int\nByteOffset: int\nValues: tuple[tuple[float, ...], ...]'),
 'Values/IndexData': ('', 'DynamicFlag: bool\nStreamIndex: int\nByteOffset: int\nIsShort: bool\nValues: tuple[int, ...]'),
 'Values/FatPoint': ('', 'Width: int\nHeight: int\nBoxSize: tuple[float, ...]'),
 'Values/SimpleMesh': ('Values.VertexData,Values.ObjectRef', 'Bounds: tuple[float, ...]\nPrimitive: int\nVertexBuffer: VertexData | None\nIndexBuffer: ObjectRef | None\nIsPlanar: bool'),
 'Values/CacheData': ('', 'ModeValue: int\nAxisValue: tuple[float, ...]\nBounds: tuple[float, ...]\nBakedMatrix: tuple[float, ...]\nMappingMatrix: tuple[float, ...]\nCylinderCap: bool | None = None\nSquareCap: bool | None = None\nWoodOrigin: tuple[float, ...] | None = None\nWoodAxis: tuple[float, ...] | None = None'),
 'Values/TextureCache': ('Values.CacheData', 'IsLayered: bool\nPrimary: CacheData\nSecondary: CacheData | None'),
 'Values/TextureValue': ('Values.EntityRef,Values.TextureCache', 'AssetName: str\nReference: EntityRef\nCache: TextureCache'),
 'Values/FieldValue': ('Values.TextureValue', 'FieldName: str\nDataValue: bool | int | float | str | None | tuple[float, ...] | TextureValue'),
 'Values/GraphicAttr': ('Values.FieldValue', 'ClassName: str\nPriority: int\nWinTies: bool\nFields: tuple[FieldValue, ...]'),
 'Values/StyleValue': ('Values.FieldValue', 'Fields: tuple[FieldValue, ...]'),
 'Nodes/NodeValue': ('Values.EntityRef,Values.SceneSet', 'NodeType: int\nRenderRef: str | None\nAttributes: SceneSet\nEntityStatus: int\nEntityLink: EntityRef | None\nQualifier: float\nClientName: str | None\nSubtypeName: str | None\nSerialId: float\nDoubleSided: int\nColorValue: tuple[float, ...]\nConsolFlags: int\nImmediateFlags: int\nRenderFlags: int\nSceneFlags: int'),
 'Nodes/NodePayload': ('Nodes.NodeValue', 'Selector: int\nDataValue: NodeValue | None\nIsXref: bool | None = None\nActEntity: int | None = None\nInstanceId: int | None = None'),
 'Nodes/RenderFrame': ('Nodes.NodeValue', 'Matrix: tuple[float, ...] | None\nNodeData: NodeValue | None'),
 'Nodes/BodyChild': ('Nodes.NodePayload', 'Matrix: tuple[float, ...] | None\nNodeData: NodePayload'),
 'Nodes/LodValue': ('Nodes.NodePayload,Values.SimpleMesh,Values.FatPoint', 'NodeData: NodePayload\nLodMask: int\nGeometry: SimpleMesh | FatPoint | None\nBounds: tuple[float, ...]\nUseClosest: bool'),
 'Nodes/BrepWorld': ('Nodes.BodyChild,Nodes.LodValue', 'EdgeGroup: BodyChild | None\nEdgeNodes: tuple[LodValue, ...]\nFaceGroup: BodyChild | None\nFaceNodes: tuple[LodValue, ...]\nModelBox: tuple[float, ...] | None'),
 'Nodes/SketchWorld': ('Nodes.BrepWorld,Nodes.LodValue', 'FaceBody: BrepWorld | None\nNodes: tuple[LodValue, ...]'),
 'Nodes/SceneWorld': ('Values.ObjectRef', 'WorldKind: str\nRevisionId: int\nPublishMode: int\nNodes: tuple[ObjectRef, ...]\nAccelerate: bool | None'),
 'Nodes/GroupValue': ('Nodes.NodePayload,Nodes.SceneWorld,Nodes.BrepWorld,Nodes.SketchWorld', 'Matrix: tuple[float, ...] | None\nNoCulling: bool\nBounds: tuple[float, ...] | None\nWorldKind: int\nWorldValue: SceneWorld | BrepWorld | SketchWorld | None\nNodeData: NodePayload'),
 'Nodes/GeoValue': ('Nodes.RenderFrame,Values.SimpleMesh,Values.FatPoint', 'Frame: RenderFrame\nGeometry: SimpleMesh | FatPoint | None\nBounds: tuple[float, ...]'),
 'Nodes/TextValue': ('Nodes.RenderFrame,Values.ObjectRef', 'Frame: RenderFrame\nMatrix: tuple[float, ...]\nEnvelope: tuple[float, ...]\nTextData: str | None\nAlignment: int\nEscapement: float\nTextStyle: ObjectRef | None\nParaStyle: ObjectRef | None\nBlockStyle: ObjectRef | None\nAnchor: tuple[float, ...]\nPriority: int'),
 'State/SceneGlobals': ('', 'Versions: tuple[tuple[str, int], ...]\nEnvironment: str'),
 'State/GraphicScene': ('State.SceneGlobals,Nodes.SceneWorld,State.SceneObject', 'Globals: SceneGlobals\nRootWorld: SceneWorld\nObjects: tuple[SceneObject, ...]'),
 'State/GraphicsStream': ('', 'StreamIndex: int\nPayload: bytes'),
 'State/GraphicsData': ('State.GraphicsStream', 'WorldData: bytes\nMeshStreams: tuple[GraphicsStream, ...]'),
}


def main():
 for target, (imports, fields) in MODELS.items():
  name=target.split('/')[-1]
  text='from dataclasses import dataclass as MakeDataClass\n'
  for imported in imports.split(',') if imports else []:
   text+=f'from {PREFIX}{imported} import {imported.split(".")[-1]}\n'
  text+=f'\n\n@MakeDataClass(frozen=True, slots=True)\nclass {name}:\n'
  text+=''.join('    '+line+'\n' for line in fields.splitlines())
  (BASE/'Model'/(target+'.py')).write_text(text)
 print(len(MODELS))


if __name__=='__main__':main()
