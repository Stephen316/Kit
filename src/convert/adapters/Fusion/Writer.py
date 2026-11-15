from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.Bridge.WritePayloadMut import WritePayloadMut
from convert.adapters.Fusion.Bridge.WriterInfo import KWriterInfo
from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentModel import CadDocument


# the fusion writer contract needs a dedicated boundary so public document claims remain grounded in native records
class FusionWriter:

    # the typed materials contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def TypedMaterials(self) -> bool:
        return True

    # the info contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def Info(self) -> AdapterInfo:
        return KWriterInfo

    info = Info

    # the supports contract needs a shared interpretation so public document claims remain grounded in native records
    def Supports(self, Document: CadDocument, Target: KTargetType) -> bool:
        return set(Document.metadata) in ({"fusion.authoring"}, {"fusion.native_state"})

    # the supports contract needs a shared interpretation so public document claims remain grounded in native records
    def supports(self, document: CadDocument, destination: KTargetType) -> bool:
        return self.Supports(document, destination)

    # the write contract needs a consistent construction rule so public document claims remain grounded in native records
    def Write(
        self,
        Document: CadDocument,
        Target: KTargetType,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        Settings = Options if Options is not None else WriteOptions()
        if (
            Settings.configuration is not None
            or Settings.destination_format not in (None, "fusion.f3d", "f3d")
            or set(Settings.values)
            - {
                "final_destination",
                "final_overwrite",
                "allow_carrier",
                "require_self_contained",
                "allow_non_native",
                "portable",
            }
        ):
            raise ValueError("Unsupported Fusion write options")
        Payload = EncodeDocument(Document)
        CapsValue = InferCaps(Document) | Document.capabilities
        if CapsValue - KWriterInfo.capabilities:
            raise ValueError("Unsupported Fusion document capabilities")

        # ordering by value value must stay deterministic so native adapter translation resolves equivalent inputs consistently
        Transfers = tuple(
            CapTransfer(Value, TransferMode.KNative)
            for Value in sorted(CapsValue, key=lambda Value: Value.value)
        )
        PathValue = WritePayloadMut(Target, Payload, Settings)
        return WriteResult(
            PathValue,
            KWriterInfo.format_id,
            len(Payload),
            transfers=Transfers,
            application_usable=True,
            vendor_loadable=True,
        )

    # the write contract needs a shared interpretation so public document claims remain grounded in native records
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.Write(document, destination, options)
