from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph


# bundle model needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleModel:
    DesignId: str
    DesignName: str
    CurrentVersion: str
    Graph: BundleGraph
    RootPath: str
