# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# changing original native points must move both the guide and the revolved solid
KAxisProbe = """
import os
import FreeCAD as App

def endpoint(axis, index):
    point = axis.Geometry[index]
    return App.Vector(point.X, point.Y, 0)

def measure(doc):
    (feature,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
    shape = feature.Shape
    assert feature.Visibility and 'Invalid' not in feature.State
    assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
    print('KIT_AXIS_REVOLVE', shape.Volume, *shape.Solids[0].CenterOfMass)
    return feature

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
measure(doc)
doc.recompute()
rev = measure(doc)
axis, sub = rev.AxisLink
assert sub == ['Edge1'] and axis.getConstruction(3) and not axis.getConstruction(4)
targets = [(11, -9, 0), (25, 27, 0)]
if os.environ['KIT_REVERSED'] == 'yes':
    targets.reverse()
for index, point in enumerate(targets, 1):
    axis.moveGeometry(index, 1, App.Vector(*point), False)
sheet = doc.getObject('Parameters')
sheet.set(sheet.getCellFromAlias('fusion_parameter_311'), '=-41 deg')
doc.recompute()
assert abs(rev.Angle + 41) < 1e-8 and len(axis.Shape.Edges) == 1
measure(doc)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
doc = App.openDocument(os.environ['KIT_ORACLE_SAVED'])
doc.recompute()
rev = measure(doc)
axis = rev.AxisLink[0]
first, second = endpoint(axis, 1), endpoint(axis, 2)
for index, point in ((1, first + App.Vector(3, -1, 0)), (2, first), (1, second)):
    axis.moveGeometry(index, 1, point, False)
doc.recompute()
assert abs(rev.Angle - 41) < 1e-8
measure(doc)
App.closeDocument(doc.Name)

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
doc.recompute()
(rev,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
axis = rev.AxisLink[0]
shift = App.Vector(-8 * (4/5)**0.5, 8 * (1/5)**0.5, 0)
for index in (1, 2):
    axis.moveGeometry(index, 1, endpoint(axis, index) + shift, False)
doc.recompute()
assert abs(rev.Angle - 73) < 1e-8
measure(doc)
doc.saveAs(os.environ['KIT_ORACLE_TOUCH'])
App.closeDocument(doc.Name)
"""
