from interchange.document.Behavior.DocumentIoBehavior import DocumentIo
from interchange.document.Behavior.DocumentLookupBehavior import DocumentLookup
from interchange.document.Behavior.DocumentValidBehavior import DocumentValid


# focused method contracts keep the immutable document schema independently reviewable
class DocumentApi(DocumentIo, DocumentValid, DocumentLookup):
    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue
