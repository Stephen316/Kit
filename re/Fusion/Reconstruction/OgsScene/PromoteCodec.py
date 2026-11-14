from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'src/convert/formats/Fusion/GraphicsCodec'
P = 'convert.formats.Fusion.GraphicsCodec.'

def save(name, code):
    path = BASE / (name + '.py')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(code).lstrip())

def model(name, fields, imports=''):
    cls = name.rsplit('/', 1)[-1]
    save('Model/' + name, 'from __future__ import annotations\nfrom dataclasses import dataclass as MakeDataClass\n' + imports + '\n\n@MakeDataClass(frozen=True, slots=True)\nclass ' + cls + ':\n' + ''.join('    ' + x + '\n' for x in fields))

model('Values/AppliedSet', ['SetValue: SceneSet', 'ApplyTypes: tuple[int, ...] | None'], f'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from {P}Model.Values.SceneSet import SceneSet\n')
model('Values/SceneSet', ['SetKind: int', 'FlagsValue: int = 0', 'RemovedFlags: int = 0', 'AppendTypes: tuple[int, ...] = ()', 'Attributes: tuple[GraphicAttr, ...] = ()', 'ExternalRef: EntityRef | None = None', 'NodeRef: str | None = None', 'ChildSets: tuple[AppliedSet, ...] = ()'], f'from {P}Model.Values.GraphicAttr import GraphicAttr\nfrom {P}Model.Values.EntityRef import EntityRef\nfrom {P}Model.Values.AppliedSet import AppliedSet\n')
model('State/SceneObject', ['Reference: ObjectRef', 'Value: KObjectValue'], f'from {P}Model.Values.ObjectRef import ObjectRef\nfrom {P}Model.State.KObjectValue import KObjectValue\n')
save('Model/State/KObjectValue', '\n'.join(f'from {P}Model.{folder}.{name} import {name}' for folder, name in [('Nodes','GroupValue'),('Nodes','GeoValue'),('Nodes','TextValue'),('Values','VertexFormat'),('Values','IndexData'),('Values','StyleValue')]) + '\n\nKObjectValue = GroupValue | GeoValue | TextValue | VertexFormat | IndexData | StyleValue\n')
path = BASE / 'Model/Nodes/GroupValue.py'
path.write_text(path.read_text().replace('    HasWorld: bool\n', '').replace('    WorldKind: int\n', '    HasWorld: bool\n    WorldKind: int\n'))
save('Wire/SceneWire', '''
from math import isfinite as IsFinite
from struct import pack as PackValue, unpack as UnpackValue, calcsize as CalcSize


class SceneWire:
    def __init__(self, Payload: bytes | None) -> None:
        self.IsReading = Payload is not None
        self.Payload = Payload or b""
        self.Position = 0
        self.Output = bytearray()

    def Transfer(self, Length: int, Value: bytes | None) -> bytes:
        if self.IsReading:
            Ending = self.Position + Length
            if Ending > len(self.Payload):
                raise ValueError("Truncated Fusion graphics stream")
            Result = self.Payload[self.Position:Ending]
            self.Position = Ending
            return Result
        if Value is None or len(Value) != Length:
            raise ValueError("Missing graphics field value")
        self.Output.extend(Value)
        return Value

    def Integer(self, Value: int | None, Format: str = "<I") -> int:
        if not self.IsReading and type(Value) is not int:
            raise ValueError("Expected an integer graphics field")
        Encoded = None if self.IsReading else PackValue(Format, Value)
        return int(UnpackValue(Format, self.Transfer(CalcSize(Format), Encoded))[0])

    def IsFlag(self, Value: bool | None) -> bool:
        if not self.IsReading and type(Value) is not bool:
            raise ValueError("Expected a boolean graphics field")
        Number = self.Integer(None if self.IsReading else int(bool(Value)), "<B")
        if Number not in (0, 1):
            raise ValueError("Noncanonical graphics boolean")
        return bool(Number)

    def Scalar(self, Value: float | None, Format: str = "<f") -> float:
        if not self.IsReading and (type(Value) is not float or not IsFinite(Value)):
            raise ValueError("Expected a finite floating graphics field")
        Encoded = None if self.IsReading else PackValue(Format, Value)
        Result = float(UnpackValue(Format, self.Transfer(CalcSize(Format), Encoded))[0])
        if not IsFinite(Result):
            raise ValueError("Nonfinite graphics field")
        return Result

    def Vector(self, Value: tuple[float, ...] | None, Count: int, Format: str = "<f") -> tuple[float, ...]:
        if not self.IsReading and (type(Value) is not tuple or len(Value) != Count):
            raise ValueError("Incorrect graphics vector length")
        return tuple(self.Scalar(None if Value is None else Value[Index], Format) for Index in range(Count))

    def CountValue(self, Value: int | None, Format: str = "<I") -> int:
        Result = self.Integer(Value, Format)
        if not 0 <= Result <= 1000000:
            raise ValueError("Graphics collection count exceeds qualified limit")
        return Result

    def TextValue(self, Value: str | None) -> str:
        if not self.IsReading and type(Value) is not str:
            raise ValueError("Expected a graphics string")
        Encoded = None if Value is None else Value.encode("utf-16le")
        Length = self.CountValue(None if Encoded is None else len(Encoded) // 2)
        return self.Transfer(Length * 2, Encoded).decode("utf-16le")

    def OptionalText(self, Value: str | None) -> str | None:
        return self.TextValue(Value) if self.IsFlag(Value is not None) else None

    def OptionalMat(self, Value: tuple[float, ...] | None) -> tuple[float, ...] | None:
        return self.Vector(Value, 16) if self.IsFlag(Value is not None) else None

    def ExpectText(self, Value: str) -> None:
        if self.TextValue(Value) != Value:
            raise ValueError("Unexpected Fusion graphics class or marker")

    def EmptyLinks(self, Count: int) -> None:
        if any(tuple(self.IsFlag(False) for _ in range(Count))):
            raise ValueError("Unsupported linked graphics callback")
''')
save('Wire/MeshStreams', '''
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream


class MeshStreams:
    def __init__(self, Streams: tuple[GraphicsStream, ...], IsReading: bool) -> None:
        self.IsReading = IsReading
        self.Inputs = {Entry.StreamIndex: Entry.Payload for Entry in Streams}
        self.Ranges: dict[int, dict[tuple[int, int], bytes]] = {}
        if len(self.Inputs) != len(Streams) or any(type(Entry.StreamIndex) is not int or not 0 <= Entry.StreamIndex < 1000 or type(Entry.Payload) is not bytes for Entry in Streams):
            raise ValueError("Invalid graphics mesh streams")

    def Transfer(self, Stream: int, Offset: int, Length: int, Payload: bytes | None) -> bytes:
        if not 0 <= Stream < 1000 or Offset < 0 or Length < 0 or Offset + Length > 67108864:
            raise ValueError("Invalid graphics buffer range")
        if self.IsReading:
            Source = self.Inputs.get(Stream)
            if Source is None or Offset + Length > len(Source):
                raise ValueError("Missing graphics buffer bytes")
            Payload = Source[Offset:Offset + Length]
        if Payload is None or len(Payload) != Length:
            raise ValueError("Incorrect graphics buffer length")
        Ranges = self.Ranges.setdefault(Stream, {})
        KeyValue = (Offset, Offset + Length)
        for (Start, Ending), Current in Ranges.items():
            if max(Start, Offset) < min(Ending, Offset + Length) and (KeyValue != (Start, Ending) or Current != Payload):
                raise ValueError("Conflicting graphics buffer ranges")
        Ranges[KeyValue] = Payload
        return Payload

    def Finalize(self) -> tuple[GraphicsStream, ...]:
        Results: list[GraphicsStream] = []
        if self.IsReading and set(self.Inputs) != set(self.Ranges):
            raise ValueError("Unreferenced graphics mesh streams")
        for Stream, Ranges in sorted(self.Ranges.items()):
            Output = bytearray()
            for (Start, Ending), Payload in sorted(Ranges.items()):
                if Start != len(Output):
                    raise ValueError("Unaccounted graphics mesh bytes")
                Output.extend(Payload)
            if self.IsReading and len(Output) != len(self.Inputs[Stream]):
                raise ValueError("Trailing graphics mesh bytes")
            Results.append(GraphicsStream(Stream, bytes(Output)))
        return tuple(Results)
''')
save('Schema/FieldRule', '''
from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FieldRule:
    FieldName: str
    WireKind: str
    ItemCount: int = 1
''')
attrs = {
'HWSelectionPostProcessingAttribute': [],
'DepthPriorityAttribute':[('DepthPriority','i32')], 'VisibilityAttribute':[('Visibility','bool')],
'TransformAttribute':[('Transform','f32',16),('Absolute','bool')],
'FColorEffectAttribute':[('Color','f32',4)],'GroupAttribute':[('GroupID','i32')],
'OrderInTransparentGroupAttribute':[('OrderInTransparentGroup','i32')],
'BillBoardAttribute':[('Style','i32'),('Anchor','f32',3),('Axis','f32',3),('Compensation','f32',3),('FlipVisibility','i32')],
'PixelScaleAttribute':[('ScreenSpaceSize','f64'),('ModelSpaceSize','f64'),('ScaleCenter','f32',3)],
'PixelScaleTranslationAttribute':[('ScreenSpaceDistance','f64'),('Translation','f32',3)],
'SelectabilityAttribute':[('Selectability','bool'),('SelectionPriority','i32'),('AlphaImageSelectionQualifier','absent')],
'FOccludedEffectAttribute':[('Color','f32',4),('ImagePartName','opt-text'),('Path','opt-text'),('VisibleOpacity','f32'),('OccludedOpacity','f32')],
'FLineStyleAttribute':[('Weight','f32'),('Space','i32'),('LinePatternName','opt-text'),('XScale','f32'),('YScale','f32')],
'TextureMappingAttribute':[('TextureMapping','texture')],
'FPrioritizedProteinAttribute':[('AssetReference','text'),('Category','u32')]}
styles = {
'TextStyle':[('Typeface','text'),('Charset','i32'),('Pitch','i32'),('Family','i32'),('IsSHX','bool'),('Color','f32',4),('Height','f32'),('Weight','i32'),('WidthFactor','f32'),('CharSacingFactor','f32'),('Italic','bool'),('ObliqueAngle','f32'),('Underline','bool'),('Strikethrough','bool'),('Overline','bool'),('BaselineOffset','f32'),('BackgroundColor','f32',4),('Orientation','f32')],
'ParagraphStyle':[('LeftIndent','f32'),('RightIndent','f32'),('FirstLineIndent','f32'),('TabStopCount','zero'),('LineSpace','f32'),('Ascent','f32'),('Descent','f32'),('AlignmentType','i32'),('LineSpaceType','i32')],
'BlockStyle':[(x,'i32') for x in ('Baseline direction','Flow direction','Baseline alignment','Flow alignment')]+[('Escapement','f32'),('IsHorizontalBaseline','bool')]}
for name, data in [('AttrRules',attrs),('StyleRules',styles)]:
    code=f'from {P}Schema.FieldRule import FieldRule\n\n\nK{name}: dict[str, tuple[FieldRule, ...]] = {{\n'
    for key, fields in data.items():
        code+='    '+repr(key)+': ('+''.join('FieldRule('+', '.join(map(repr, f))+'), ' for f in fields)+'),\n'
    save('Schema/'+name,code+'}\n')
save('Schema/GlobalVersions', '''
KGlobalVersions = {
    "TextureMappingAttribute": 1,
    "TextureEffectAttribute": 1,
    "NodeData": 2,
    "GraphicsBlobFeatures": 1,
    "F360InstanceNode": 1,
    "BillBoardAttribute": 2,
    "GroupNode": 1,
    "GraphicsGlobalVersion": 1,
    "OGSBlobVersion": 0,
}
''')

def func(name, models, code, extra=''):
    imports='from __future__ import annotations\nfrom typing import TYPE_CHECKING\n'+extra+'\n'
    for folder, model_name in models:
        imports+=f'from {P}Model.{folder}.{model_name} import {model_name}\n'
    imports+=f'\nif TYPE_CHECKING:\n    from {P}Wire.SceneCodec import SceneCodec\n\n\n'
    save(name,imports+dedent(code).lstrip())

func('Values/XferCacheMut',[('Values','CacheData')],'''
def XferCacheMut(State: SceneCodec, Value: CacheData | None) -> CacheData:
    ModeValue = State.Integer(Value.ModeValue if Value else None, "<i")
    if ModeValue not in range(7):
        raise ValueError("Unsupported graphics texture mapping mode")
    AxisValue = State.Vector(Value.AxisValue if Value else None, 3, "<d")
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    BakedMatrix = State.Vector(Value.BakedMatrix if Value else None, 16, "<d")
    MappingMatrix = State.Vector(Value.MappingMatrix if Value else None, 16, "<d")
    CylinderCap = State.IsFlag(Value.CylinderCap if Value else None) if ModeValue == 4 else None
    SquareCap = State.IsFlag(Value.SquareCap if Value else None) if ModeValue == 4 else None
    WoodOrigin = State.Vector(Value.WoodOrigin if Value else None, 3, "<d") if ModeValue == 6 else None
    WoodAxis = State.Vector(Value.WoodAxis if Value else None, 3, "<d") if ModeValue == 6 else None
    Result = CacheData(ModeValue, AxisValue, Bounds, BakedMatrix, MappingMatrix, CylinderCap, SquareCap, WoodOrigin, WoodAxis)
    State.CheckResult(Value, Result)
    return Result
''')
func('Values/XferTextureMut',[('Values','TextureValue'),('Values','TextureCache'),('Values','EntityRef')],'''
def XferTextureMut(State: SceneCodec, Value: TextureValue | None) -> TextureValue | None:
    if not State.IsFlag(Value is not None):
        return None
    AssetName = State.TextValue(Value.AssetName if Value else None)
    SegmentId = State.Integer(Value.Reference.SegmentId if Value else None)
    ObjectId = State.Integer(Value.Reference.ObjectId if Value else None, ">Q")
    IsLayered = State.IsFlag(Value.Cache.IsLayered if Value else None)
    Primary = XferCacheMut(State, Value.Cache.Primary if Value else None)
    Secondary = None
    if State.IsFlag(Value is not None and Value.Cache.Secondary is not None):
        Secondary = XferCacheMut(State, Value.Cache.Secondary if Value else None)
    return TextureValue(AssetName, EntityRef(SegmentId, ObjectId), TextureCache(IsLayered, Primary, Secondary))
''',f'from {P}Values.XferCacheMut import XferCacheMut\n')
func('Fields/XferFieldMut',[('Values','FieldValue'),('Values','TextureValue')],'''
def XferFieldMut(State: SceneCodec, Rule: FieldRule, Value: FieldValue | None) -> FieldValue:
    Current = Value.DataValue if Value else None
    if Rule.WireKind == "texture":
        if Current is not None and not isinstance(Current, TextureValue):
            raise ValueError("Expected typed graphics texture mapping")
        Result = XferTextureMut(State, Current)
    elif Rule.WireKind == "absent":
        State.EmptyLinks(1)
        Result = None
    elif Rule.WireKind == "zero":
        Result = State.Integer(CastValue(int | None, Current))
        if Result:
            raise ValueError("Unsupported nonempty graphics tab stops")
    elif Rule.WireKind == "bool":
        Result = State.IsFlag(CastValue(bool | None, Current))
    elif Rule.WireKind in ("i32", "u32"):
        Result = State.Integer(CastValue(int | None, Current), "<i" if Rule.WireKind == "i32" else "<I")
    elif Rule.WireKind in ("f32", "f64"):
        Format = "<f" if Rule.WireKind == "f32" else "<d"
        Result = State.Scalar(CastValue(float | None, Current), Format) if Rule.ItemCount == 1 else State.Vector(CastValue(tuple[float, ...] | None, Current), Rule.ItemCount, Format)
    elif Rule.WireKind == "text":
        Result = State.TextValue(CastValue(str | None, Current))
    elif Rule.WireKind == "opt-text":
        Result = State.OptionalText(CastValue(str | None, Current))
    else:
        raise ValueError("Unsupported graphics field descriptor")
    return FieldValue(Rule.FieldName, Result)
''',f'from typing import cast as CastValue\nfrom {P}Schema.FieldRule import FieldRule\nfrom {P}Values.XferTextureMut import XferTextureMut\n')
func('Fields/XferFieldsMut',[('Values','FieldValue')],'''
def XferFieldsMut(State: SceneCodec, Rules: tuple[FieldRule, ...], Values: tuple[FieldValue, ...] | None) -> tuple[FieldValue, ...]:
    if not State.IsReading and (Values is None or tuple(Entry.FieldName for Entry in Values) != tuple(Entry.FieldName for Entry in Rules)):
        raise ValueError("Incorrect graphics fields or field order")
    return tuple(XferFieldMut(State, Rule, Values[Index] if Values else None) for Index, Rule in enumerate(Rules))
''',f'from {P}Schema.FieldRule import FieldRule\nfrom {P}Fields.XferFieldMut import XferFieldMut\n')
func('Fields/XferAttrMut',[('Values','GraphicAttr')],'''
def XferAttrMut(State: SceneCodec, Value: GraphicAttr | None) -> GraphicAttr:
    ClassName = State.TextValue(Value.ClassName if Value else None)
    Rules = KAttrRules.get(ClassName)
    if Rules is None:
        raise ValueError("Unsupported graphics attribute class")
    Priority = State.Integer(Value.Priority if Value else None, "<i")
    WinTies = State.IsFlag(Value.WinTies if Value else None)
    Fields = XferFieldsMut(State, Rules, Value.Fields if Value else None)
    return GraphicAttr(ClassName, Priority, WinTies, Fields)
''',f'from {P}Schema.AttrRules import KAttrRules\nfrom {P}Fields.XferFieldsMut import XferFieldsMut\n')
func('Fields/XferStyleMut',[('Values','StyleValue')],'''
def XferStyleMut(State: SceneCodec, ClassName: str, Value: StyleValue | None) -> StyleValue:
    Rules = KStyleRules.get(ClassName)
    if Rules is None:
        raise ValueError("Unsupported graphics text style")
    return StyleValue(XferFieldsMut(State, Rules, Value.Fields if Value else None))
''',f'from {P}Schema.StyleRules import KStyleRules\nfrom {P}Fields.XferFieldsMut import XferFieldsMut\n')
func('Fields/XferSetBaseMut',[('Values','SceneSet')],'''
def XferSetBaseMut(State: SceneCodec, Value: SceneSet | None, SetKind: int) -> SceneSet:
    FlagsValue = State.Integer(Value.FlagsValue if Value else None)
    RemovedFlags = State.Integer(Value.RemovedFlags if Value else None)
    AppendCount = State.CountValue(len(Value.AppendTypes) if Value else None)
    AppendTypes = tuple(State.Integer(Value.AppendTypes[Index] if Value else None) for Index in range(AppendCount))
    AttrCount = State.CountValue(len(Value.Attributes) if Value else None, "<i")
    Attributes = tuple(XferAttrMut(State, Value.Attributes[Index] if Value else None) for Index in range(AttrCount))
    return SceneSet(SetKind, FlagsValue, RemovedFlags, AppendTypes, Attributes)
''',f'from {P}Fields.XferAttrMut import XferAttrMut\n')
func('Fields/XferChildSetMut',[('Values','AppliedSet')],'''
def XferChildSetMut(State: SceneCodec, Value: AppliedSet | None) -> AppliedSet:
    IsSpecific = State.IsFlag(Value is not None and Value.ApplyTypes is not None)
    SetValue = XferSetBaseMut(State, Value.SetValue if Value else None, 2)
    ApplyTypes = None
    if IsSpecific:
        Values = Value.ApplyTypes if Value else None
        Count = State.CountValue(len(Values) if Values is not None else None)
        ApplyTypes = tuple(State.Integer(Values[Index] if Values is not None else None) for Index in range(Count))
    return AppliedSet(SetValue, ApplyTypes)
''',f'from {P}Fields.XferSetBaseMut import XferSetBaseMut\n')
func('Fields/XferSetMut',[('Values','SceneSet'),('Values','EntityRef')],'''
def XferSetMut(State: SceneCodec, Value: SceneSet | None) -> SceneSet:
    SetKind = State.Integer(Value.SetKind if Value else None, "<i")
    if SetKind in (0, 1):
        Result = SceneSet(SetKind)
    elif SetKind in (2, 3):
        Result = XferSetBaseMut(State, Value, SetKind)
        if SetKind == 3:
            ExternalRef, NodeRef = None, None
            if State.IsFlag(Value is not None and Value.ExternalRef is not None):
                Target = Value.ExternalRef if Value else None
                ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
                SegmentId = State.Integer(Target.SegmentId if Target else None)
                ExternalRef = EntityRef(SegmentId, ObjectId)
            else:
                NodeRef = State.TextValue(Value.NodeRef if Value else None)
                State.NodeLinks.add(NodeRef)
            Count = State.CountValue(len(Value.ChildSets) if Value else None, "<i")
            Children = tuple(XferChildSetMut(State, Value.ChildSets[Index] if Value else None) for Index in range(Count))
            Result = ReplaceValue(Result, ExternalRef=ExternalRef, NodeRef=NodeRef, ChildSets=Children)
    else:
        raise ValueError("Unsupported graphics attribute set")
    State.CheckResult(Value, Result)
    return Result
''',f'from dataclasses import replace as ReplaceValue\nfrom {P}Fields.XferSetBaseMut import XferSetBaseMut\nfrom {P}Fields.XferChildSetMut import XferChildSetMut\n')
func('Nodes/XferNodeMut',[('Nodes','NodeValue'),('Values','EntityRef')],'''
def XferNodeMut(State: SceneCodec, Value: NodeValue | None, IsQuick: bool) -> NodeValue:
    NodeType = State.Integer(Value.NodeType if Value else None)
    RenderRef = None if IsQuick else State.TextValue(Value.RenderRef if Value else None)
    if RenderRef is not None:
        if RenderRef != State.ActiveNode:
            raise ValueError("Graphics node data references a different render node")
        State.NodeLinks.add(RenderRef)
    Attributes = XferSetMut(State, Value.Attributes if Value else None)
    EntityStatus = State.Integer(Value.EntityStatus if Value else None, "<i")
    EntityLink = None
    if EntityStatus in (1, 2):
        Target = Value.EntityLink if Value else None
        SegmentId = State.Integer(Target.SegmentId if Target else None)
        ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
        EntityLink = EntityRef(SegmentId, ObjectId)
    elif EntityStatus != 0:
        raise ValueError("Unsupported graphics entity status")
    Qualifier = State.Scalar(Value.Qualifier if Value else None, "<d")
    ClientName = State.OptionalText(Value.ClientName if Value else None)
    SubtypeName = State.OptionalText(Value.SubtypeName if Value else None)
    SerialId = State.Scalar(Value.SerialId if Value else None, "<d")
    if any(Number < 0 or Number > 2 ** 53 or Number != int(Number) for Number in (Qualifier, SerialId)):
        raise ValueError("Graphics identity exceeds exact numeric range")
    DoubleSided = State.Integer(Value.DoubleSided if Value else None)
    ColorValue = State.Vector(Value.ColorValue if Value else None, 4)
    ConsolFlags = State.Integer(Value.ConsolFlags if Value else None)
    ImmediateFlags = State.Integer(Value.ImmediateFlags if Value else None, "<i")
    RenderFlags = State.Integer(Value.RenderFlags if Value else None)
    SceneFlags = State.Integer(Value.SceneFlags if Value else None)
    Result = NodeValue(NodeType, RenderRef, Attributes, EntityStatus, EntityLink, Qualifier, ClientName, SubtypeName, SerialId, DoubleSided, ColorValue, ConsolFlags, ImmediateFlags, RenderFlags, SceneFlags)
    State.CheckResult(Value, Result)
    return Result
''',f'from {P}Fields.XferSetMut import XferSetMut\n')
func('Nodes/XferPayloadMut',[('Nodes','NodePayload')],'''
def XferPayloadMut(State: SceneCodec, Value: NodePayload | None) -> NodePayload:
    Selector = State.Integer(Value.Selector if Value else None)
    DataValue, IsXref, ActEntity, InstanceId = None, None, None, None
    if Selector in (2, 3, 4, 5, 6, 7):
        DataValue = XferNodeMut(State, Value.DataValue if Value else None, True)
        if Selector == 4:
            IsXref = State.IsFlag(Value.IsXref if Value else None)
            if IsXref:
                ActEntity = State.Integer(Value.ActEntity if Value else None, ">Q")
            InstanceId = State.Integer(Value.InstanceId if Value else None)
    elif Selector:
        raise ValueError("Unsupported graphics node data serializer")
    Result = NodePayload(Selector, DataValue, IsXref, ActEntity, InstanceId)
    State.CheckResult(Value, Result)
    return Result
''',f'from {P}Nodes.XferNodeMut import XferNodeMut\n')
func('Nodes/XferFrameMut',[('Nodes','RenderFrame')],'''
def XferFrameMut(State: SceneCodec, Value: RenderFrame | None) -> RenderFrame:
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(4)
    NodeData = None
    if State.IsFlag(Value is not None and Value.NodeData is not None):
        State.ExpectText("NodeData")
        NodeData = XferNodeMut(State, Value.NodeData if Value else None, False)
    return RenderFrame(Matrix, NodeData)
''',f'from {P}Nodes.XferNodeMut import XferNodeMut\n')
func('Nodes/XferChildMut',[('Nodes','BodyChild')],'''
def XferChildMut(State: SceneCodec, Value: BodyChild | None) -> BodyChild:
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(3)
    return BodyChild(Matrix, XferPayloadMut(State, Value.NodeData if Value else None))
''',f'from {P}Nodes.XferPayloadMut import XferPayloadMut\n')
func('Nodes/XferLodMut',[('Nodes','LodValue')],'''
def XferLodMut(State: SceneCodec, Value: LodValue | None) -> LodValue:
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    LodMask = State.Integer(Value.LodMask if Value else None)
    Geometry = None
    if LodMask:
        if LodMask & (LodMask - 1) or State.Integer(0) != 0:
            raise ValueError("Unsupported graphics display item or LOD set")
        Geometry = XferGeometryMut(State, Value.Geometry if Value else None)
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    UseClosest = State.IsFlag(Value.UseClosest if Value else None)
    Result = LodValue(NodeData, LodMask, Geometry, Bounds, UseClosest)
    State.CheckResult(Value, Result)
    return Result
''',f'from {P}Nodes.XferPayloadMut import XferPayloadMut\nfrom {P}Geometry.XferGeometryMut import XferGeometryMut\n')
func('Nodes/XferBrepMut',[('Nodes','BrepWorld')],'''
def XferBrepMut(State: SceneCodec, Value: BrepWorld | None) -> BrepWorld:
    EdgeGroup, FaceGroup = None, None
    EdgeNodes, FaceNodes = (), ()
    if State.IsFlag(Value is not None and Value.EdgeGroup is not None):
        EdgeGroup = XferChildMut(State, Value.EdgeGroup if Value else None)
        EdgeCount = State.CountValue(len(Value.EdgeNodes) if Value else None)
        EdgeNodes = tuple(XferLodMut(State, Value.EdgeNodes[Index] if Value else None) for Index in range(EdgeCount))
        FaceGroup = XferChildMut(State, Value.FaceGroup if Value else None)
        FaceCount = State.CountValue(len(Value.FaceNodes) if Value else None)
        FaceNodes = tuple(XferLodMut(State, Value.FaceNodes[Index] if Value else None) for Index in range(FaceCount))
    ModelBox = State.Vector(Value.ModelBox if Value else None, 6, "<d") if State.IsFlag(Value is not None and Value.ModelBox is not None) else None
    Result = BrepWorld(EdgeGroup, EdgeNodes, FaceGroup, FaceNodes, ModelBox)
    State.CheckResult(Value, Result)
    return Result
''',f'from {P}Nodes.XferChildMut import XferChildMut\nfrom {P}Nodes.XferLodMut import XferLodMut\n')
func('Nodes/XferSketchMut',[('Nodes','SketchWorld')],'''
def XferSketchMut(State: SceneCodec, Value: SketchWorld | None) -> SketchWorld:
    FaceBody = XferBrepMut(State, Value.FaceBody if Value else None) if State.IsFlag(Value is not None and Value.FaceBody is not None) else None
    LodCount = State.CountValue(len(Value.Nodes) if Value else None, "<i")
    if State.Integer(0, "<i"):
        raise ValueError("Unsupported ordinary sketch graphics nodes")
    Nodes = tuple(XferLodMut(State, Value.Nodes[Index] if Value else None) for Index in range(LodCount))
    if State.Integer(0, "<i"):
        raise ValueError("Unsupported nonculling sketch graphics nodes")
    return SketchWorld(FaceBody, Nodes)
''',f'from {P}Nodes.XferBrepMut import XferBrepMut\nfrom {P}Nodes.XferLodMut import XferLodMut\n')
func('Nodes/XferGeoNodeMut',[('Nodes','GeoValue')],'''
def XferGeoNodeMut(State: SceneCodec, Value: GeoValue | None) -> GeoValue:
    Frame = XferFrameMut(State, Value.Frame if Value else None)
    Geometry = XferGeometryMut(State, Value.Geometry if Value else None)
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    State.EmptyLinks(1)
    return GeoValue(Frame, Geometry, Bounds)
''',f'from {P}Nodes.XferFrameMut import XferFrameMut\nfrom {P}Geometry.XferGeometryMut import XferGeometryMut\n')
func('Nodes/XferTextMut',[('Nodes','TextValue')],'''
def XferTextMut(State: SceneCodec, Value: TextValue | None) -> TextValue:
    Frame = XferFrameMut(State, Value.Frame if Value else None)
    Matrix = State.Vector(Value.Matrix if Value else None, 16)
    Envelope = State.Vector(Value.Envelope if Value else None, 2)
    TextData = State.OptionalText(Value.TextData if Value else None)
    Alignment = State.Integer(Value.Alignment if Value else None, "<i")
    Escapement = State.Scalar(Value.Escapement if Value else None)
    TextStyle = State.LinkedObject("TextStyle", Value.TextStyle if Value else None)
    ParaStyle = State.LinkedObject("ParagraphStyle", Value.ParaStyle if Value else None)
    BlockStyle = State.LinkedObject("BlockStyle", Value.BlockStyle if Value else None)
    Anchor = State.Vector(Value.Anchor if Value else None, 2)
    Priority = State.Integer(Value.Priority if Value else None, "<i")
    return TextValue(Frame, Matrix, Envelope, TextData, Alignment, Escapement, TextStyle, ParaStyle, BlockStyle, Anchor, Priority)
''',f'from {P}Nodes.XferFrameMut import XferFrameMut\n')
func('Geometry/XferFormatMut',[('Values','VertexFormat'),('Values','VertexField')],'''
def XferFormatMut(State: SceneCodec, Value: VertexFormat | None) -> VertexFormat:
    Count = State.CountValue(len(Value.Fields) if Value else None, "<i")
    Fields = []
    for Index in range(Count):
        Current = Value.Fields[Index] if Value else None
        Fields.append(VertexField(State.Integer(Current.TypeCode if Current else None, "<i"), State.Integer(Current.UsageCode if Current else None, "<i"), State.Integer(Current.WordOffset if Current else None, "<i"), State.Integer(Current.StreamIndex if Current else None, "<i"), State.Integer(Current.UsageIndex if Current else None, "<i"), State.Integer(Current.InstanceMode if Current else None, "<i")))
    Result = VertexFormat(tuple(Fields))
    _ = VertexStride(Result)
    return Result
''',f'from {P}Geometry.VertexStride import VertexStride\n')
save('Geometry/VertexStride',f'''
from {P}Model.Values.VertexFormat import VertexFormat


def VertexStride(Value: VertexFormat) -> int:
    Fields = tuple((Entry.TypeCode, Entry.UsageCode, Entry.WordOffset, Entry.StreamIndex, Entry.UsageIndex, Entry.InstanceMode) for Entry in Value.Fields)
    if Fields == ((2, 0, 0, 0, 0, 0),):
        return 3
    if Fields == ((2, 0, 0, 0, 0, 0), (2, 1, 3, 0, 0, 0), (1, 2, 6, 0, 0, 0)):
        return 8
    raise ValueError("Unsupported graphics vertex field layout")
''')
func('Geometry/XferIndicesMut',[('Values','IndexData')],'''
def XferIndicesMut(State: SceneCodec, Value: IndexData | None) -> IndexData:
    DynamicFlag = State.IsFlag(Value.DynamicFlag if Value else None)
    StreamIndex = State.Integer(Value.StreamIndex if Value else None, "<i")
    ByteOffset = State.Integer(Value.ByteOffset if Value else None, "<i")
    ByteLength = State.Integer(len(Value.Values) * (2 if Value.IsShort else 4) if Value else None, "<i")
    WidthFlag = State.Integer(int(Value.IsShort) if Value else None, "<i")
    if WidthFlag not in (0, 1):
        raise ValueError("Unsupported graphics index width")
    IsShort = bool(WidthFlag)
    WidthValue = 2 if IsShort else 4
    if ByteLength <= 0 or ByteLength % WidthValue:
        raise ValueError("Incomplete graphics index buffer")
    Format = "<" + ("H" if IsShort else "I") * (ByteLength // WidthValue)
    if Value is not None and (type(Value.IsShort) is not bool or any(type(Number) is not int for Number in Value.Values)):
        raise ValueError("Expected integer graphics indices")
    Payload = PackValue(Format, *Value.Values) if Value else None
    Encoded = State.MeshData.Transfer(StreamIndex, ByteOffset, ByteLength, Payload)
    return IndexData(DynamicFlag, StreamIndex, ByteOffset, IsShort, tuple(int(Number) for Number in UnpackValue(Format, Encoded)))
''','from struct import pack as PackValue, unpack as UnpackValue\n')
func('Geometry/XferVerticesMut',[('Values','VertexData'),('Values','VertexFormat')],'''
def XferVerticesMut(State: SceneCodec, Value: VertexData | None) -> VertexData:
    DynamicFlag = State.IsFlag(Value.DynamicFlag if Value else None)
    FormatRef = State.LinkedObject("VertexFormat", Value.FormatRef if Value else None)
    if FormatRef is None:
        raise ValueError("Graphics vertices require an explicit vertex format")
    FormatValue = State.ObjectValues[FormatRef]
    if not isinstance(FormatValue, VertexFormat):
        raise ValueError("Graphics vertex format has an incompatible class")
    WidthValue = VertexStride(FormatValue)
    if State.Integer(1, "<i") != 1:
        raise ValueError("Unsupported multiple graphics vertex streams")
    StreamIndex = State.Integer(Value.StreamIndex if Value else None, "<i")
    ByteOffset = State.Integer(Value.ByteOffset if Value else None, "<i")
    ByteLength = State.Integer(len(Value.Values) * WidthValue * 4 if Value else None, "<i")
    if ByteLength <= 0 or ByteLength % (4 * WidthValue):
        raise ValueError("Incomplete graphics vertex buffer")
    Format = "<" + "f" * (ByteLength // 4)
    Payload = PackVertices(Value, WidthValue, Format)
    Encoded = State.MeshData.Transfer(StreamIndex, ByteOffset, ByteLength, Payload)
    Numbers = tuple(float(Number) for Number in UnpackValue(Format, Encoded))
    if not all(IsFinite(Number) for Number in Numbers):
        raise ValueError("Nonfinite graphics vertex")
    Values = tuple(Numbers[Index:Index + WidthValue] for Index in range(0, len(Numbers), WidthValue))
    return VertexData(DynamicFlag, FormatRef, StreamIndex, ByteOffset, Values)
''',f'from math import isfinite as IsFinite\nfrom struct import unpack as UnpackValue\nfrom {P}Geometry.VertexStride import VertexStride\nfrom {P}Geometry.PackVertices import PackVertices\n')
save('Geometry/PackVertices',f'''
from math import isfinite as IsFinite
from struct import pack as PackValue
from {P}Model.Values.VertexData import VertexData


def PackVertices(Value: VertexData | None, Width: int, Format: str) -> bytes | None:
    if Value is None:
        return None
    if type(Value.Values) is not tuple or any(type(Vertex) is not tuple or len(Vertex) != Width for Vertex in Value.Values):
        raise ValueError("Invalid graphics vertex dimensions")
    Numbers = tuple(Number for Vertex in Value.Values for Number in Vertex)
    if any(type(Number) is not float or not IsFinite(Number) for Number in Numbers):
        raise ValueError("Expected finite floating graphics vertices")
    return PackValue(Format, *Numbers)
''')
func('Geometry/XferMeshMut',[('Values','SimpleMesh'),('Values','IndexData')],'''
def XferMeshMut(State: SceneCodec, Value: SimpleMesh | None) -> SimpleMesh:
    Bounds = State.Vector(Value.Bounds if Value else None, 6)
    Primitive = State.Integer(Value.Primitive if Value else None, "<i")
    if Primitive not in (2, 3, 4):
        raise ValueError("Unsupported graphics primitive topology")
    VertexBuffer = XferVerticesMut(State, Value.VertexBuffer if Value else None) if State.IsFlag(Value is not None and Value.VertexBuffer is not None) else None
    IndexBuffer = State.LinkedObject("AIndexBuffer", Value.IndexBuffer if Value else None)
    IsPlanar = State.IsFlag(Value.IsPlanar if Value else None)
    if IndexBuffer is not None:
        Indices = State.ObjectValues[IndexBuffer]
        if not isinstance(Indices, IndexData) or VertexBuffer is None or any(Index >= len(VertexBuffer.Values) for Index in Indices.Values):
            raise ValueError("Graphics indices do not address their vertex buffer")
    return SimpleMesh(Bounds, Primitive, VertexBuffer, IndexBuffer, IsPlanar)
''',f'from {P}Geometry.XferVerticesMut import XferVerticesMut\n')
func('Geometry/XferGeometryMut',[('Values','SimpleMesh'),('Values','FatPoint')],'''
def XferGeometryMut(State: SceneCodec, Value: SimpleMesh | FatPoint | None) -> SimpleMesh | FatPoint | None:
    if not State.IsFlag(Value is not None):
        return None
    KindValue = "FatPointMesh" if isinstance(Value, FatPoint) else "OgsSimpleMesh"
    ClassName = State.TextValue(KindValue)
    if ClassName == "OgsSimpleMesh":
        return XferMeshMut(State, Value if isinstance(Value, SimpleMesh) else None)
    if ClassName == "FatPointMesh":
        Current = Value if isinstance(Value, FatPoint) else None
        Width = State.Integer(Current.Width if Current else None, "<i")
        Height = State.Integer(Current.Height if Current else None, "<i")
        BoxSize = State.Vector(Current.BoxSize if Current else None, 3)
        return FatPoint(Width, Height, BoxSize)
    raise ValueError("Unsupported graphics geometry class")
''',f'from {P}Geometry.XferMeshMut import XferMeshMut\n')
func('Worlds/XferGlobalMut',[('State','SceneGlobals')],'''
def XferGlobalMut(State: SceneCodec, Value: SceneGlobals | None) -> SceneGlobals:
    Count = State.CountValue(len(Value.Versions) if Value else None)
    Versions = []
    for Index in range(Count):
        ClassName = State.TextValue(Value.Versions[Index][0] if Value else None)
        Version = State.Integer(Value.Versions[Index][1] if Value else None)
        Versions.append((ClassName, Version))
    Environment = State.TextValue(Value.Environment if Value else None)
    if len(Versions) != len(KGlobalVersions) or dict(Versions) != KGlobalVersions or Environment != "RiverRubicon":
        raise ValueError("Unsupported graphics serializer versions or environment")
    return SceneGlobals(tuple(Versions), Environment)
''',f'from {P}Schema.GlobalVersions import KGlobalVersions\n')
func('Worlds/XferWorldMut',[('Nodes','SceneWorld'),('Values','ObjectRef')],'''
def XferWorldMut(State: SceneCodec, Value: SceneWorld | None, IsRoot: bool = False) -> SceneWorld:
    WorldKind = State.TextValue(Value.WorldKind if Value else None)
    if WorldKind not in ("ARenderList", "SingleNodeWorld"):
        raise ValueError("Unsupported graphics world class")
    Revision = State.Integer(Value.RevisionId if Value else None)
    PublishMode = State.Integer(Value.PublishMode if Value else None, "<i")
    if Revision != 5 or PublishMode != 1:
        raise ValueError("Unsupported graphics world revision or publish mode")
    Nodes: list[ObjectRef] = []
    while True:
        Current = Value.Nodes[len(Nodes)] if Value and len(Nodes) < len(Value.Nodes) else None
        ClassName = State.TextValue(Current.ClassName if Current else "WorldSerializerEndMark")
        if ClassName == "WorldSerializerEndMark":
            break
        if ClassName not in ("GroupNode", "GeometryNode", "FTextNode") or len(Nodes) >= 1000000:
            raise ValueError("Unsupported world node class or count")
        Nodes.append(State.ObjectValue(ClassName, Current))
    Accelerate = State.IsFlag(Value.Accelerate if Value else None) if WorldKind == "ARenderList" and not IsRoot else None
    Result = SceneWorld(WorldKind, Revision, PublishMode, tuple(Nodes), Accelerate)
    State.CheckResult(Value, Result)
    return Result
''')
func('Worlds/XferGroupMut',[('Nodes','GroupValue'),('Nodes','SceneWorld'),('Nodes','BrepWorld'),('Nodes','SketchWorld')],'''
def XferGroupMut(State: SceneCodec, Value: GroupValue | None) -> GroupValue:
    if not State.HasGlobals:
        State.Globals = XferGlobalMut(State, State.Globals)
        State.HasGlobals = True
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(3)
    NoCulling = State.IsFlag(Value.NoCulling if Value else None)
    Bounds = None if NoCulling else State.Vector(Value.Bounds if Value else None, 6, "<d")
    HasWorld = State.IsFlag(Value.HasWorld if Value else None)
    WorldKind, WorldValue = 0, None
    Current = Value.WorldValue if Value else None
    if HasWorld:
        WorldKind = State.Integer(Value.WorldKind if Value else None)
        if WorldKind == 0:
            if State.IsFlag(Current is not None):
                WorldValue = XferWorldMut(State, Current if isinstance(Current, SceneWorld) else None)
        elif WorldKind == 1:
            WorldValue = XferBrepMut(State, Current if isinstance(Current, BrepWorld) else None)
        elif WorldKind == 3:
            WorldValue = XferSketchMut(State, Current if isinstance(Current, SketchWorld) else None)
        else:
            raise ValueError("Unsupported custom graphics world")
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    Result = GroupValue(Matrix, NoCulling, Bounds, HasWorld, WorldKind, WorldValue, NodeData)
    State.CheckResult(Value, Result)
    return Result
''',f'from {P}Worlds.XferGlobalMut import XferGlobalMut\nfrom {P}Worlds.XferWorldMut import XferWorldMut\nfrom {P}Nodes.XferPayloadMut import XferPayloadMut\nfrom {P}Nodes.XferBrepMut import XferBrepMut\nfrom {P}Nodes.XferSketchMut import XferSketchMut\n')
func('Wire/XferObjectMut',[('State','KObjectValue'),('Nodes','GroupValue'),('Nodes','GeoValue'),('Nodes','TextValue'),('Values','VertexFormat'),('Values','IndexData'),('Values','StyleValue')],'''
def XferObjectMut(State: SceneCodec, ClassName: str, Value: KObjectValue | None) -> KObjectValue:
    if ClassName == "GroupNode" and (Value is None or isinstance(Value, GroupValue)):
        return XferGroupMut(State, Value)
    if ClassName == "GeometryNode" and (Value is None or isinstance(Value, GeoValue)):
        return XferGeoNodeMut(State, Value)
    if ClassName == "FTextNode" and (Value is None or isinstance(Value, TextValue)):
        return XferTextMut(State, Value)
    if ClassName == "VertexFormat" and (Value is None or isinstance(Value, VertexFormat)):
        return XferFormatMut(State, Value)
    if ClassName == "AIndexBuffer" and (Value is None or isinstance(Value, IndexData)):
        return XferIndicesMut(State, Value)
    if ClassName in KStyleRules and (Value is None or isinstance(Value, StyleValue)):
        return XferStyleMut(State, ClassName, Value)
    raise ValueError("Unsupported or inconsistent graphics object class")
''','\n'.join(f'from {P}{folder}.{name} import {name}' for folder,name in [('Worlds','XferGroupMut'),('Nodes','XferGeoNodeMut'),('Nodes','XferTextMut'),('Geometry','XferFormatMut'),('Geometry','XferIndicesMut'),('Fields','XferStyleMut')])+f'\nfrom {P}Schema.StyleRules import KStyleRules\n')
save('Wire/SceneCodec',f'''
from re import fullmatch as FullMatch
from {P}Model.State.GraphicScene import GraphicScene
from {P}Model.State.GraphicsStream import GraphicsStream
from {P}Model.State.KObjectValue import KObjectValue
from {P}Model.State.SceneGlobals import SceneGlobals
from {P}Model.State.SceneObject import SceneObject
from {P}Model.Values.ObjectRef import ObjectRef
from {P}Wire.SceneWire import SceneWire
from {P}Wire.MeshStreams import MeshStreams
from {P}Wire.XferObjectMut import XferObjectMut


class SceneCodec(SceneWire):
    def __init__(self, Payload: bytes | None, Streams: tuple[GraphicsStream, ...], Scene: GraphicScene | None) -> None:
        super().__init__(Payload)
        self.MeshData = MeshStreams(Streams, self.IsReading)
        self.Globals: SceneGlobals | None = Scene.Globals if Scene else None
        self.HasGlobals = False
        self.InputObjects = {{Entry.Reference: Entry.Value for Entry in Scene.Objects}} if Scene else {{}}
        self.ObjectValues: dict[ObjectRef, KObjectValue] = {{}}
        self.ObjectKinds: dict[str, str] = {{}}
        self.NodeLinks: set[str] = set()
        self.ActiveNode: str | None = None
        self.Depth = 0
        if Scene and len(self.InputObjects) != len(Scene.Objects):
            raise ValueError("Duplicate graphics object definitions")

    def CheckResult(self, Value: object, Result: object) -> None:
        if not self.IsReading and Value != Result:
            raise ValueError("Graphics model contains unsupported or inconsistent fields")

    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        ObjectId = self.TextValue(Value.ObjectId if Value else None)
        if FullMatch(r"0x[0-9a-fA-F]+", ObjectId) is None:
            raise ValueError("Invalid graphics object identity")
        Result = ObjectRef(ClassName, ObjectId)
        self.CheckResult(Value, Result)
        Existing = self.ObjectKinds.get(ObjectId)
        if Existing is not None:
            if Existing != ClassName:
                raise ValueError("Graphics object identity has conflicting classes")
            return Result
        if self.Depth >= 128 or len(self.ObjectKinds) >= 1000000:
            raise ValueError("Graphics object graph exceeds qualified limits")
        Current = self.InputObjects.get(Result)
        if not self.IsReading and Current is None:
            raise ValueError("Undefined graphics object reference")
        self.ObjectKinds[ObjectId] = ClassName
        Previous = self.ActiveNode
        self.ActiveNode = ObjectId
        self.Depth += 1
        Parsed = XferObjectMut(self, ClassName, Current)
        self.Depth -= 1
        self.ActiveNode = Previous
        self.CheckResult(Current, Parsed)
        self.ObjectValues[Result] = Parsed
        return Result

    def LinkedObject(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef | None:
        if not self.IsFlag(Value is not None):
            return None
        self.ExpectText(ClassName)
        return self.ObjectValue(ClassName, Value)

    def Finalize(self) -> tuple[SceneObject, ...]:
        if not self.HasGlobals:
            raise ValueError("Graphics world has no serializer version declaration")
        if self.IsReading and self.Position != len(self.Payload):
            raise ValueError("Trailing Fusion graphics world bytes")
        if not self.IsReading and set(self.InputObjects) != set(self.ObjectValues):
            raise ValueError("Unreachable graphics object definitions")
        if any(self.ObjectKinds.get(Handle) not in ("GroupNode", "GeometryNode", "FTextNode") for Handle in self.NodeLinks):
            raise ValueError("Unresolved or incompatible graphics node reference")
        return tuple(SceneObject(Reference, Value) for Reference, Value in self.ObjectValues.items())
''')
save('ReadGraphics',f'''
from struct import error as StructError
from {P}Model.State.GraphicScene import GraphicScene
from {P}Model.State.GraphicsStream import GraphicsStream
from {P}Wire.SceneCodec import SceneCodec
from {P}Worlds.XferWorldMut import XferWorldMut


def ReadGraphics(WorldData: bytes, MeshStreams: tuple[GraphicsStream, ...]) -> GraphicScene:
    if type(WorldData) is not bytes or len(WorldData) > 67108864:
        raise ValueError("Invalid graphics world input")
    try:
        State = SceneCodec(WorldData, MeshStreams, None)
        RootWorld = XferWorldMut(State, None, True)
        Objects = State.Finalize()
        _ = State.MeshData.Finalize()
        if State.Globals is None:
            raise ValueError("Missing graphics serializer versions")
        return GraphicScene(State.Globals, RootWorld, Objects)
    except (StructError, UnicodeError, OverflowError) as Error:
        raise ValueError("Invalid Fusion graphics wire field") from Error
''')
save('EmitGraphics',f'''
from struct import error as StructError
from {P}Model.State.GraphicScene import GraphicScene
from {P}Model.State.GraphicsData import GraphicsData
from {P}Wire.SceneCodec import SceneCodec
from {P}Worlds.XferWorldMut import XferWorldMut


def EmitGraphics(Value: GraphicScene) -> GraphicsData:
    if not isinstance(Value, GraphicScene):
        raise ValueError("Expected a typed Fusion graphics scene")
    try:
        State = SceneCodec(None, (), Value)
        _ = XferWorldMut(State, Value.RootWorld, True)
        _ = State.Finalize()
        Streams = State.MeshData.Finalize()
        return GraphicsData(bytes(State.Output), Streams)
    except (StructError, UnicodeError, OverflowError) as Error:
        raise ValueError("Invalid Fusion graphics model field") from Error
''')
