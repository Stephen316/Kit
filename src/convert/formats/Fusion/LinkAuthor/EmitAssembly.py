from dataclasses import replace as Replace

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.LinkAuthor.Building.ActBuild import ActRecordSet, EditAct
from convert.formats.Fusion.LinkAuthor.Building.BrowserBuild import (
    BrowserSet,
    EditBrowser,
)
from convert.formats.Fusion.LinkAuthor.Building.ClassBind import ExtendSegment
from convert.formats.Fusion.LinkAuthor.Building.DesignBuild import DesignRecords
from convert.formats.Fusion.LinkAuthor.Building.DesignEdits import EditDesign
from convert.formats.Fusion.LinkAuthor.Building.LinkTables import (
    AssetLinks,
    LinkContexts,
    ManifestLinks,
)
from convert.formats.Fusion.LinkAuthor.CheckAsmSpec import CheckAsmSpec
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Planning.PlanKeys import PlanKeys
from convert.formats.Fusion.LinkAuthor.Reading.DocSegment import SegmentOf
from convert.formats.Fusion.LinkAuthor.Reading.ReadRoot import ReadRoot
from convert.formats.Fusion.LinkAuthor.Reading.ReadTarget import ReadTarget
from convert.formats.Fusion.MetaIndex import SegmentKind

KLinkKinds = (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)


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


def EmitAssembly(Request: AssemblySpec) -> bytes:
    Checked = CheckAsmSpec(Request)
    return EmitParsed(LinkDocument(ReadDocument(EmitDocument(Checked.Base)), Checked))
