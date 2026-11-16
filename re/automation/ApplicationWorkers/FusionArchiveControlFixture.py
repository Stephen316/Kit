import os
from pathlib import Path
from types import SimpleNamespace

from ApplicationProtocol import encoded, write_new

CONTROL = Path(
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


# the disposable process runs the real pinned control code against these vendor API objects
def attach_control(app, fusion, repo):
    fixture = ControlFixture(app, repo / CONTROL)
    fusion.CalculationAccuracy = SimpleNamespace(VeryHighCalculationAccuracy=1)
    fusion.DesignTypes = SimpleNamespace(ParametricDesignType=1)
    fusion.Design = SimpleNamespace(cast=lambda design: design)
    app.importManager = fixture


class ControlFixture:
    def __init__(self, app, source):
        self.app = app
        self.source = source
        self.open_marker = app.root / "document-open"

    def createFusionArchiveImportOptions(self, source):
        assert Path(source) == self.source and source.endswith(".f3d")
        assert (self.app.root / "exercise-archive-control").is_file()
        return SimpleNamespace(source=source, isViewFit=True)

    def importToNewDocument(self, options):
        assert options.source == str(self.source) and options.isViewFit is False
        assert self.app.documents.count == 0
        write_new(
            self.app.root / "fixture-control-imported", encoded({"pid": os.getpid()})
        )
        self.open_marker.touch(exist_ok=False)
        design = self.design()
        return SimpleNamespace(
            products=SimpleNamespace(itemByProductType=lambda role: design),
            close=self.close,
        )

    def design(self):
        point = SimpleNamespace(x=0, y=0, z=0)
        empty = SimpleNamespace(count=0)
        body = SimpleNamespace(
            name="Control",
            isSolid=True,
            volume=30.0,
            boundingBox=SimpleNamespace(minPoint=point, maxPoint=point),
            faces=empty,
            edges=empty,
            vertices=empty,
        )
        component = SimpleNamespace(
            sketches=empty,
            bRepBodies=SimpleNamespace(count=1, item=lambda index: body),
            getPhysicalProperties=lambda accuracy: SimpleNamespace(centerOfMass=point),
        )
        return SimpleNamespace(
            rootComponent=component,
            designType=1,
            timeline=empty,
            allParameters=empty,
            fusionUnitsManager=SimpleNamespace(distanceDisplayUnits="mm"),
            computeAll=self.recompute,
        )

    def recompute(self):
        assert self.open_marker.is_file()
        write_new(
            self.app.root / "fixture-control-recomputed", encoded({"pid": os.getpid()})
        )
        return True

    def close(self, save):
        assert save is False
        self.open_marker.unlink()
        write_new(
            self.app.root / "fixture-control-closed", encoded({"pid": os.getpid()})
        )
