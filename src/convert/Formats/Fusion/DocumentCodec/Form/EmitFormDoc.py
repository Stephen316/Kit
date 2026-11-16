from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano
from uuid import uuid4 as MakeUuid

from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Converted.CreateFormBrep import (
    CreateFormBrep,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import (
    FormMarks,
)
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.EmitFormPart import (
    EmitFormPart,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KFormFolder
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.Formats.Fusion.DocumentCodec.Form.BuildFormDesign import BuildFormDesign
from convert.Formats.Fusion.DocumentCodec.Form.CheckFormSpec import CheckFormSpec
from convert.Formats.Fusion.DocumentCodec.Form.FormParts import MakeFormParts
from convert.Formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

# boundary representation folder must remain consistent across callers so editable control cages retain their document relationships
KBrepFolder = "Breps.BlobParts/"


# the form doc operation needs a consistent construction rule so editable control cages retain their document relationships
def EmitFormDoc(SpecValue: FormSpec) -> bytes:
    CheckFormSpec(SpecValue)
    Parts = MakeFormParts()
    Stamp = GeometryStamp(
        "Kit", "Fusion native document codec", DateTime.now(UTC).isoformat()
    )
    Marks = FormMarks(Stamp, ReadTimeNano() // 1000)
    Converted = CreateFormBrep(SpecValue.Surface, SpecValue.Body, Marks)
    Design = BuildFormDesign(SpecValue, str(MakeUuid()), Parts, Marks.UnixMicros)
    Payloads = (
        ContainerPart(KBrepFolder + Parts.History, EmitJournal(Converted.History)),
        EmitSnapPart(DocumentSnap(KBrepFolder + Parts.Snapshot, Converted.Snapshot)),
        EmitFormPart(DocumentForm(KFormFolder + Parts.Cage, SpecValue.Surface)),
    )
    return PackDocument(Design, SpecValue.Title, Payloads + BuildMatPart(Design))
