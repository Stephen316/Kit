# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# native checks distinguish cached edge order and sweep phase from volume alone
KBodyProbe = """
import os
import FreeCAD as App

def measure(doc):
    (seed,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Extrusion']
    (rev,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
    assert rev.AxisLink == (seed, [os.environ['KIT_AXIS_EDGE']])
    edge = seed.getSubObject(rev.AxisLink[1][0])
    assert edge is not None and len(edge.Vertexes) == 2
    assert abs((edge.Vertexes[1].Point - edge.Vertexes[0].Point).dot(App.Vector(0,0,1))) < 1e-8
    for obj in (seed, rev):
        assert obj.Visibility and 'Invalid' not in obj.State
        assert obj.Shape.isValid() and obj.Shape.isClosed() and len(obj.Shape.Solids) == 1
    print('KIT_BODY_REV', seed.Shape.Volume, rev.Shape.Volume, *rev.Shape.CenterOfMass)
    return rev

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
measure(doc)
doc.recompute()
rev = measure(doc)
assert abs(rev.Angle + 73) < 1e-8
sheet = doc.getObject('Parameters')
sheet.set(sheet.getCellFromAlias('fusion_parameter_251'), '=-3 mm')
sheet.set(sheet.getCellFromAlias('fusion_parameter_355'), '=-41 deg')
doc.recompute()
assert abs(rev.Angle + 41) < 1e-8
measure(doc)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
doc = App.openDocument(os.environ['KIT_ORACLE_SAVED'])
doc.recompute()
measure(doc)
App.closeDocument(doc.Name)
"""
