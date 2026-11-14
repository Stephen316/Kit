from pathlib import Path as FilePath

from convert.formats.Fusion.ContainerCodec.Browser.BrowserFields import BrowserFields
from convert.formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.formats.Fusion.ContainerCodec.Browser.BrowserRootMap import BrowserRootMap
from convert.formats.Fusion.ContainerCodec.Browser.CheckBrowRoles import CheckBrowRoles
from convert.formats.Fusion.ContainerCodec.Browser.ComponentLinks import KComponentLinks
from convert.formats.Fusion.ContainerCodec.Browser.DesignReference import (
    DesignReference,
)
from convert.formats.Fusion.ContainerCodec.Browser.ObserverCounts import ObserverCounts
from convert.formats.Fusion.ContainerCodec.Graph.ExternalProfile import ExternalProfile
from convert.formats.Fusion.ContainerCodec.Graph.SegmentBuilder import SegmentBuilder
from convert.formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import SegmentKind


def BuildBrowser(Design: DesignResult, Assembly: AuxiliaryGraph) -> AuxiliaryGraph:
    CheckBrowRoles(Design)
    if Assembly.Streams.SegmentId != 1:
        raise ValueError("Fusion browser requires the active assembly segment")
    Schemas = ReadVocabulary(FilePath(__file__).with_name("BrowserClasses.json"))
    External = ExternalProfile(Assembly.Profile, Assembly.Records, 1)
    Profile = EntityProfile(
        External.RootGuid,
        External.Classes,
        (*Assembly.Profile.ExternalTargets, *External.ExternalTargets),
    )
    Builder = SegmentBuilder(SegmentKind.KBrowser, Schemas, Profile)
    Roles = {
        Entry.RoleName: Index for Index, Entry in enumerate(KBrowserNodes, 201)
    } | {"root": 200}
    Builder.AddEntity(
        200,
        "FusionComponentBrowserRoot",
        BrowserRootMap(Design, Roles),
        "PersistBrowserRootId",
        SplitIndex=3,
    )
    Counts = ObserverCounts(Design.Records)
    for Entry in KBrowserNodes:
        Links = KComponentLinks.get(Entry.RoleName, ())
        Targets = Links + ((Entry.TargetRole,) if Entry.TargetRole is not None else ())
        Subjects: list[SubjectValue] = []
        for RoleName in Targets:
            Identity = Design.Roles[RoleName]
            Subjects.append(
                SubjectValue(DesignReference(Design, RoleName), Counts.get(Identity, 0))
            )
            Counts[Identity] = Counts.get(Identity, 0) + 1
        Builder.AddEntity(
            Roles[Entry.RoleName],
            Entry.ClassName,
            BrowserFields(Design, Roles, Entry),
            Subjects=tuple(Subjects),
        )
    return Builder.Finish()
