import queue as EventQueue
import runpy as ScriptRun
import sys as System
import time as Clock
from collections.abc import Callable
from pathlib import Path as FilePath
from types import ModuleType, SimpleNamespace


# the callback must execute on the same thread that loaded the real addin
class StubFusion:

    # an open document stops the real counterpart before it can call any cad method
    def __init__(self) -> None:
        super().__init__()
        self.version = "fixture.no-native-runtime"
        self.documents = SimpleNamespace(count=1)
        self.Events: EventQueue.Queue[str] = EventQueue.Queue()
        self.Notify: Callable[[SimpleNamespace], None] | None = None
        setattr(self, "registerCustomEvent", self.RegisterEvent)
        setattr(self, "unregisterCustomEvent", self.Unregister)
        setattr(self, "fireCustomEvent", self.FireEvent)
        setattr(self, "add", self.AddHandler)

    # registration is sufficient for the real addin to retain its custom event handler
    def RegisterEvent(self, EventId: str) -> "StubFusion":
        assert EventId == "KitCaptureRunnerJob"
        return self

    # teardown must unregister the same event without invoking a native application
    def Unregister(self, EventId: str) -> None:
        assert EventId == "KitCaptureRunnerJob"

    # callback custody remains with the real addin rather than a simulated queue host
    def AddHandler(self, Handler: object) -> None:
        self.Notify = getattr(Handler, "notify")

    # events cross the real background poller boundary before reaching the main thread
    def FireEvent(self, EventId: str, RawEvent: str) -> bool:
        assert EventId == "KitCaptureRunnerJob"
        self.Events.put(RawEvent)
        return True


# the only fake boundary is the application event surface before any native work
def RunFixture(Bootstrap: FilePath, DoneFlag: FilePath) -> None:
    Application = StubFusion()

    # startup must discover the same object that receives the scheduled events
    def GetApp() -> StubFusion:
        return Application

    Autodesk = ModuleType("adsk")
    CoreModule = ModuleType("adsk.core")
    setattr(CoreModule, "Application", SimpleNamespace(get=GetApp))
    setattr(CoreModule, "CustomEventHandler", object)
    setattr(Autodesk, "core", CoreModule)
    System.modules["adsk"] = Autodesk
    System.modules["adsk.core"] = CoreModule
    Runner = ScriptRun.run_path(str(Bootstrap))
    Runner["run"]({})
    try:
        Deadline = Clock.monotonic() + 160
        while not DoneFlag.exists() and Clock.monotonic() < Deadline:
            try:
                RawEvent = Application.Events.get(timeout=0.2)
            except EventQueue.Empty:
                continue
            assert Application.Notify is not None
            Application.Notify(SimpleNamespace(additionalInfo=RawEvent))
        assert DoneFlag.exists(), "disposable Fusion fixture reached its deadline"
    finally:
        Runner["stop"]({})
        Runner["state"]["thread"].join(timeout=5)


if __name__ == "__main__":
    RunFixture(FilePath(System.argv[1]), FilePath(System.argv[2]))
