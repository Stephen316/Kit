from pathlib import Path as FilePath

from convert.Formats.Fusion.ContainerCodec.Browser.BrowserFields import BrowserFields
from convert.Formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.Formats.Fusion.ContainerCodec.Browser.BrowserRootMap import BrowserRootMap
from convert.Formats.Fusion.ContainerCodec.Browser.CheckBrowRoles import CheckBrowRoles
from convert.Formats.Fusion.ContainerCodec.Browser.ComponentLinks import KComponentLinks
from convert.Formats.Fusion.ContainerCodec.Browser.DesignReference import (
    DesignReference,
)
from convert.Formats.Fusion.ContainerCodec.Browser.ObserverCounts import ObserverCounts
from convert.Formats.Fusion.ContainerCodec.Graph.ExternalProfile import ExternalProfile
from convert.Formats.Fusion.ContainerCodec.Graph.SegmentBuilder import SegmentBuilder
from convert.Formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.MetaIndex import SegmentKind


# the browser operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
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
