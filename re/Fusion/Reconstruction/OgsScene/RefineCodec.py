from pathlib import Path
from textwrap import dedent
BASE=Path(__file__).resolve().parents[4]/'src/convert/formats/Fusion/GraphicsCodec'
P='convert.formats.Fusion.GraphicsCodec.'
def put(name,code):
 (BASE/(name+'.py')).write_text(dedent(code).lstrip())
def read(name):return (BASE/(name+'.py')).read_text()
def method(text,name):
 start=text.index('    def '+name+'(')
 end=text.find('\n    def ',start+1)
 return text[start:end if end>=0 else len(text)].rstrip()+'\n'
wire=read('Wire/SceneWire')
put('Wire/ByteStream', 'from struct import pack as PackValue, unpack as UnpackValue, calcsize as CalcSize\n\n\nclass ByteStream:\n'+''.join(method(wire,n)+'\n' for n in ['__init__','Transfer','Integer']))
put('Wire/NumericWire', 'from math import isfinite as IsFinite\nfrom struct import pack as PackValue, unpack as UnpackValue, calcsize as CalcSize\n'+f'from {P}Wire.ByteStream import ByteStream\n\n\nclass NumericWire(ByteStream):\n'+''.join(method(wire,n)+'\n' for n in ['IsFlag','Scalar','Vector']))
put('Wire/SceneWire', f'from {P}Wire.NumericWire import NumericWire\n\n\nclass SceneWire(NumericWire):\n'+''.join(method(wire,n)+'\n' for n in ['CountValue','TextValue','OptionalText','OptionalMat','ExpectText','EmptyLinks']))
mesh=read('Wire/MeshStreams')
transfer=method(mesh,'Transfer').replace('    def Transfer(','def TransferSpanMut(').replace('        ','    ').replace('self,','State: MeshStreams,').replace('self.','State.')
finish=method(mesh,'Finalize').replace('    def Finalize(','def FinishStreams(').replace('        ','    ').replace('self)','State: MeshStreams)').replace('self.','State.')
header='from __future__ import annotations\nfrom typing import TYPE_CHECKING\n'+f'from {P}Model.State.GraphicsStream import GraphicsStream\n\nif TYPE_CHECKING:\n    from {P}Wire.MeshStreams import MeshStreams\n\n\n'
put('Wire/TransferSpanMut',header+transfer)
put('Wire/FinishStreams',header+finish)
put('Wire/MeshStreams',f'from {P}Model.State.GraphicsStream import GraphicsStream\nfrom {P}Wire.TransferSpanMut import TransferSpanMut\nfrom {P}Wire.FinishStreams import FinishStreams\n\n\nclass MeshStreams:\n'+method(mesh,'__init__')+'''
    def Transfer(self, Stream: int, Offset: int, Length: int, Payload: bytes | None) -> bytes:
        return TransferSpanMut(self, Stream, Offset, Length, Payload)

    def Finalize(self) -> tuple[GraphicsStream, ...]:
        return FinishStreams(self)
''')
scene=read('Wire/SceneCodec')
headers=scene[:scene.index('class SceneCodec')].replace('from re import fullmatch as FullMatch\n','').replace(f'from {P}Wire.XferObjectMut import XferObjectMut\n','').replace(f'from {P}Model.State.SceneObject import SceneObject\n','')
put('Wire/SceneState',headers+'class SceneState(SceneWire):\n'+method(scene,'__init__')+'\n'+method(scene,'CheckResult'))
obj=method(scene,'ObjectValue').replace('    def ObjectValue(','def ObjectValueMut(').replace('        ','    ').replace('self,','State: SceneCodec,').replace('self.','State.').replace('XferObjectMut(self,','XferObjectMut(State,')
finish=method(scene,'Finalize').replace('    def Finalize(','def FinishScene(').replace('        ','    ').replace('self)','State: SceneCodec)').replace('self.','State.')
header='from __future__ import annotations\nfrom typing import TYPE_CHECKING\n'+f'from {P}Model.Values.ObjectRef import ObjectRef\n\nif TYPE_CHECKING:\n    from {P}Wire.SceneCodec import SceneCodec\n\n\n'
put('Wire/ObjectValueMut',header.replace('\n\nif TYPE_CHECKING:',f'\nfrom re import fullmatch as FullMatch\nfrom {P}Wire.XferObjectMut import XferObjectMut\n\nif TYPE_CHECKING:')+obj)
put('Wire/FinishScene',header.replace(f'from {P}Model.Values.ObjectRef import ObjectRef',f'from {P}Model.State.SceneObject import SceneObject')+finish)
put('Wire/SceneCodec',f'from {P}Wire.SceneState import SceneState\nfrom {P}Wire.ObjectValueMut import ObjectValueMut\nfrom {P}Wire.FinishScene import FinishScene\nfrom {P}Model.Values.ObjectRef import ObjectRef\nfrom {P}Model.State.SceneObject import SceneObject\n\n\nclass SceneCodec(SceneState):\n'+'''
    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        return ObjectValueMut(self, ClassName, Value)

'''+method(scene,'LinkedObject')+'''
    def Finalize(self) -> tuple[SceneObject, ...]:
        return FinishScene(self)
''')
for name in ['Fields/XferFieldMut','Fields/XferFieldsMut']:
 s=read(name);import re;s=re.sub(r'\bRule\b','FieldRuleValue',s);put(name,s)
s=read('Fields/XferFieldMut').replace('    Current =','    Result: bool | int | float | str | None | tuple[float, ...] | TextureValue\n    Current =');put('Fields/XferFieldMut',s)
s=read('Geometry/XferIndicesMut').replace('from struct import','from typing import cast as CastValue\nfrom struct import').replace('type(Value.IsShort) is not bool','type(CastValue(object, Value.IsShort)) is not bool');put('Geometry/XferIndicesMut',s)
s=read('Nodes/XferBrepMut').replace('    EdgeNodes, FaceNodes = (), ()','    EdgeNodes: tuple[LodValue, ...] = ()\n    FaceNodes: tuple[LodValue, ...] = ()').replace('from typing import TYPE_CHECKING','from typing import TYPE_CHECKING\n'+f'from {P}Model.Nodes.LodValue import LodValue');put('Nodes/XferBrepMut',s)
s=read('Worlds/XferGroupMut').replace('    WorldKind, WorldValue = 0, None','    WorldKind = 0\n    WorldValue: SceneWorld | BrepWorld | SketchWorld | None = None');put('Worlds/XferGroupMut',s)
s=read('Nodes/XferNodeMut')
start=s.index('    EntityStatus =');end=s.index('    Qualifier =',start)
body=s[start:end].replace('    EntityStatus = State.Integer(Value.EntityStatus if Value else None, "<i")','    EntityStatus = State.Integer(Status, "<i")').replace('        Target = Value.EntityLink if Value else None\n','')
put('Values/XferEntityMut',f'from __future__ import annotations\nfrom typing import TYPE_CHECKING\nfrom {P}Model.Values.EntityRef import EntityRef\n\nif TYPE_CHECKING:\n    from {P}Wire.SceneCodec import SceneCodec\n\n\ndef XferEntityMut(State: SceneCodec, Status: int | None, Target: EntityRef | None) -> tuple[int, EntityRef | None]:\n'+body+'    return EntityStatus, EntityLink\n')
s=s[:start]+'    EntityStatus, EntityLink = XferEntityMut(State, Value.EntityStatus if Value else None, Value.EntityLink if Value else None)\n'+s[end:]
s=s.replace(f'from {P}Model.Values.EntityRef import EntityRef',f'from {P}Values.XferEntityMut import XferEntityMut');put('Nodes/XferNodeMut',s)
