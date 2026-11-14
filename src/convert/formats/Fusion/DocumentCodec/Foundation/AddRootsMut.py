from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Defaults.SettingsPolicy import SettingsPolicy


def AddRootsMut(Author: AuthorState) -> None:
    Author.Allocate(
        "settings",
        "CommonDataAssetSettings",
        RootName="AssetSettings",
        Fields=SettingsPolicy(),
    )
    Author.Allocate("protein", "ProteinAssetManager", RootName="ProteinAssetManager")
    Author.Allocate(
        "component", "FusionComponent", ParentRole="root_instance", NamedPairs=[]
    )
    Author.Allocate("components_root", "ComponentsRoot", RootName="ComponentsRoot")
    Author.Allocate(
        "root_instance",
        "ComponentInstance",
        RootName="rootInstance",
        NamedPairs=[],
        Subjects=["component"],
    )
    Author.Allocate(
        "instances_root", "ComponentInstancesRoot", RootName="ComponentInstancesRoot"
    )
    Author.Allocate("thread_settings", "ThreadSettings")
    Author.Allocate("units", "UnitSystems", RootName="UnitSystems")
    Author.Allocate("unit_system", "UnitSystem", ParentRole="units")
    Author.Allocate("pmi_settings", "PMISettings")
    Author.Allocate("named_views", "NamedViews")
    Author.Allocate("named_lights", "NamedLights")
    Author.Allocate(
        "tracked", "NamedTrackedEntitySet", RootName="NamedTrackedEntitySet"
    )
    Author.Allocate(
        "placeholder",
        "WorkingModelPlaceholderRoot",
        RootName="WorkingModelPlaceholderRoot",
    )
    Author.Allocate(
        "post_office", "ComponentPostOffice", RootName="ComponentPostOffice"
    )
    Author.Allocate("scene_serializer", "OGSSerializer", RootName="OGSSerializer")
