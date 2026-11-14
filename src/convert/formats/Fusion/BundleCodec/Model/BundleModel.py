from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph


@MakeDataClass(frozen=True, slots=True)
class BundleModel:
    DesignId: str
    DesignName: str
    CurrentVersion: str
    Graph: BundleGraph
    RootPath: str
