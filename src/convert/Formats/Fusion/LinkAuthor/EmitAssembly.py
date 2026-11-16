from dataclasses import replace as Replace

from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.Formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.Formats.Fusion.LinkAuthor.Building.ActBuild import ActRecordSet, EditAct
from convert.Formats.Fusion.LinkAuthor.Building.BrowserBuild import (
    BrowserSet,
    EditBrowser,
)
from convert.Formats.Fusion.LinkAuthor.Building.ClassBind import ExtendSegment
from convert.Formats.Fusion.LinkAuthor.Building.DesignBuild import DesignRecords
from convert.Formats.Fusion.LinkAuthor.Building.DesignEdits import EditDesign
from convert.Formats.Fusion.LinkAuthor.Building.LinkTables import (
    AssetLinks,
    LinkContexts,
    ManifestLinks,
)
from convert.Formats.Fusion.LinkAuthor.CheckAsmSpec import CheckAsmSpec
from convert.Formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.Formats.Fusion.LinkAuthor.Planning.PlanKeys import PlanKeys
from convert.Formats.Fusion.LinkAuthor.Reading.DocSegment import SegmentOf
from convert.Formats.Fusion.LinkAuthor.Reading.ReadRoot import ReadRoot
from convert.Formats.Fusion.LinkAuthor.Reading.ReadTarget import ReadTarget
from convert.Formats.Fusion.MetaIndex import SegmentKind

# the link kinds order must stay explicit so cross document references retain their intended ownership
KLinkKinds = (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)


# the rebuild profiles contract needs a shared interpretation so cross document references retain their intended ownership
def RebuildProfiles(Segments: tuple[ParsedSegment, ...]) -> tuple[ParsedSegment, ...]:
    Schemas = ReadDocSchemas()
    Metadata = tuple(Segment.Metadata for Segment in Segments)
    return tuple(
        Replace(
            Segment,
            Profile=MakeDocProfile(
                Schemas, Metadata, Segment.Metadata.Header.SegmentId
            ),
        )
        for Segment in Segments
    )


# link document must resolve unambiguously so cross document references retain their intended ownership
def LinkDocument(BaseSpec: DocumentModel, Request: AssemblySpec) -> DocumentModel:
    if (
        tuple(Segment.Metadata.Header.Segment for Segment in BaseSpec.Segments)
        != KLinkKinds
    ):
        raise ValueError("Fusion assembly base needs design, ACT and browser segments")
    RootInfo = ReadRoot(BaseSpec)
    Facts = tuple(ReadTarget(Target.Target) for Target in Request.Targets)
    Design, Tracking, Browser = (
        SegmentOf(BaseSpec, KindValue) for KindValue in KLinkKinds
    )
    Starts = (Design.Metadata.NextId, Tracking.Metadata.NextId, Browser.Metadata.NextId)
    Scheme = PlanKeys(RootInfo, Request, Facts, Starts)
    Segments = (
        ExtendSegment(
            Design,
            EditDesign(Design.Records, RootInfo, Scheme),
            DesignRecords(RootInfo, Facts, Request, Scheme),
            (
                Scheme.DesignNext,
                LinkContexts(Request, Scheme, Facts, SegmentKind.KDesign),
            ),
        ),
        ExtendSegment(
            Tracking,
            EditAct(Tracking.Records, RootInfo, Scheme),
            ActRecordSet(RootInfo, Facts, Request, Scheme),
            (Scheme.ActNext, LinkContexts(Request, Scheme, Facts, SegmentKind.KAct)),
        ),
        ExtendSegment(
            Browser,
            EditBrowser(Browser.Records, RootInfo, Scheme),
            BrowserSet(RootInfo, Facts, Request, Scheme),
            (
                Scheme.BrowserNext,
                LinkContexts(Request, Scheme, Facts, SegmentKind.KBrowser),
            ),
        ),
    )
    return Replace(
        BaseSpec,
        Document=Replace(BaseSpec.Document, Links=ManifestLinks(Request, Scheme)),
        Asset=Replace(BaseSpec.Asset, Links=AssetLinks(Request, Scheme)),
        Segments=RebuildProfiles(Segments),
    )


# the assembly operation needs a consistent construction rule so cross document references retain their intended ownership
def EmitAssembly(Request: AssemblySpec) -> bytes:
    Checked = CheckAsmSpec(Request)
    return EmitParsed(LinkDocument(ReadDocument(EmitDocument(Checked.Base)), Checked))
