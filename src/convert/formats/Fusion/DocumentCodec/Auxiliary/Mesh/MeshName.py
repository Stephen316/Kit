from uuid import UUID as UuidValue

from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import KMeshFolder


def MeshName(Value: str) -> str:
    Prefix = KMeshFolder + "ParaMeshGeometry."
    if not Value.startswith(Prefix) or not Value.endswith(".paramesh"):
        raise ValueError("Unsupported document mesh part name")
    Identity = Value[len(Prefix) : -len(".paramesh")]
    if str(UuidValue(Identity)).lower() != Identity.lower():
        raise ValueError("Invalid document mesh part UUID")
    return Value.removeprefix(KMeshFolder)
