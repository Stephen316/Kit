from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CreateFormBrep import (
    CreateFormBrep,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import (
    FormMarks,
)
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.EmitFormPart import (
    EmitFormPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KFormFolder
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.formats.Fusion.DocumentCodec.Form.BuildFormDesign import BuildFormDesign
from convert.formats.Fusion.DocumentCodec.Form.CheckFormSpec import CheckFormSpec
from convert.formats.Fusion.DocumentCodec.Form.FormParts import MakeFormParts
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

KBrepFolder = "Breps.BlobParts/"


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
