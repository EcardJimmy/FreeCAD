# ***************************************************************************
# *   (c) 2020 Carlo Pavan                                                  *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""This module provides the object code for Draft DimensionStyle.
"""
## @package style_dimension
# \ingroup DRAFT
# \brief This module provides the object code for Draft DimensionStyle.

import FreeCAD as App
import math
from PySide.QtCore import QT_TRANSLATE_NOOP
import draftutils.gui_utils as gui_utils
import draftutils.utils as utils
from draftobjects.draft_annotation import DimensionBase
from draftviewproviders.view_dimension import ViewProviderLinearDimension

def make_dimension(p1,p2,p3=None,p4=None):
    """makeDimension(p1,p2,[p3]) or makeDimension(object,i1,i2,p3)
    or makeDimension(objlist,indices,p3): Creates a Dimension object with
    the dimension line passign through p3.The current line width and color
    will be used. There are multiple  ways to create a dimension, depending on
    the arguments you pass to it:
    - (p1,p2,p3): creates a standard dimension from p1 to p2
    - (object,i1,i2,p3): creates a linked dimension to the given object,
    measuring the distance between its vertices indexed i1 and i2
    - (object,i1,mode,p3): creates a linked dimension
    to the given object, i1 is the index of the (curved) edge to measure,
    and mode is either "radius" or "diameter".
    """
    if not App.ActiveDocument:
        App.Console.PrintError("No active document. Aborting\n")
        return
    obj = App.ActiveDocument.addObject("App::FeaturePython","Dimension")
    LinearDimension(obj)
    if App.GuiUp:
        ViewProviderLinearDimension(obj.ViewObject)
    if isinstance(p1,App.Vector) and isinstance(p2,App.Vector):
        obj.Start = p1
        obj.End = p2
        if not p3:
            p3 = p2.sub(p1)
            p3.multiply(0.5)
            p3 = p1.add(p3)
    elif isinstance(p2,int) and isinstance(p3,int):
        l = []
        idx = (p2,p3)
        l.append((p1,"Vertex"+str(p2+1)))
        l.append((p1,"Vertex"+str(p3+1)))
        obj.LinkedGeometry = l
        obj.Support = p1
        p3 = p4
        if not p3:
            v1 = obj.Base.Shape.Vertexes[idx[0]].Point
            v2 = obj.Base.Shape.Vertexes[idx[1]].Point
            p3 = v2.sub(v1)
            p3.multiply(0.5)
            p3 = v1.add(p3)
    elif isinstance(p3,str):
        l = []
        l.append((p1,"Edge"+str(p2+1)))
        if p3 == "radius":
            #l.append((p1,"Center"))
            if App.GuiUp:
                obj.ViewObject.Override = "R $dim"
            obj.Diameter = False
        elif p3 == "diameter":
            #l.append((p1,"Diameter"))
            if App.GuiUp:
                obj.ViewObject.Override = "Ø $dim"
            obj.Diameter = True
        obj.LinkedGeometry = l
        obj.Support = p1
        p3 = p4
        if not p3:
            p3 = p1.Shape.Edges[p2].Curve.Center.add(App.Vector(1,0,0))
    obj.Dimline = p3
    if hasattr(App,"DraftWorkingPlane"):
        normal = App.DraftWorkingPlane.axis
    else:
        normal = App.Vector(0,0,1)
    if App.GuiUp:
        # invert the normal if we are viewing it from the back
        vnorm = gui_utils.get3DView().getViewDirection()
        if vnorm.getAngle(normal) < math.pi/2:
            normal = normal.negative()
    obj.Normal = normal
    if App.GuiUp:
        gui_utils.format_object(obj)
        gui_utils.select(obj)

    return obj

class LinearDimension(DimensionBase):
    """The Draft Dimension object"""
    def __init__(self, obj):
        DimensionBase.__init__(self,obj,"Dimension")
        
        # Draft
        obj.addProperty("App::PropertyVectorDistance","Start",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "Startpoint of dimension"))

        obj.addProperty("App::PropertyVectorDistance","End",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "Endpoint of dimension"))

        obj.addProperty("App::PropertyVector","Normal",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The normal direction of this dimension"))

        obj.addProperty("App::PropertyVector","Direction",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The normal direction of this dimension"))

        obj.addProperty("App::PropertyVectorDistance","Dimline",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "Point through which the dimension line passes"))

        obj.addProperty("App::PropertyLink","Support",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The object measured by this dimension"))

        obj.addProperty("App::PropertyLinkSubList","LinkedGeometry",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The geometry this dimension is linked to"))

        obj.addProperty("App::PropertyLength","Distance",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The measurement of this dimension"))

        obj.addProperty("App::PropertyBool","Diameter",
                        "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "For arc/circle measurements, false = radius, true = diameter"))
        obj.Start = App.Vector(0,0,0)
        obj.End = App.Vector(1,0,0)
        obj.Dimline = App.Vector(0,1,0)
        obj.Normal = App.Vector(0,0,1)

    def onChanged(self,obj,prop):
        if hasattr(obj, "Distance"):
            obj.setEditorMode('Distance', 1)
        #if hasattr(obj,"Normal"):
        #    obj.setEditorMode('Normal', 2)
        if hasattr(obj, "Support"):
            obj.setEditorMode('Support', 2)
        if prop == "DimensionStyle":
            if hasattr(obj, "DimensionStyle"):
                gui_utils.format_object(target = obj, origin = obj.DimensionStyle)


    def execute(self, obj):
        import DraftGeomUtils
        # set start point and end point according to the linked geometry
        if obj.LinkedGeometry:
            if len(obj.LinkedGeometry) == 1:
                lobj = obj.LinkedGeometry[0][0]
                lsub = obj.LinkedGeometry[0][1]
                if len(lsub) == 1:
                    if "Edge" in lsub[0]:
                        n = int(lsub[0][4:])-1
                        edge = lobj.Shape.Edges[n]
                        if DraftGeomUtils.geomType(edge) == "Line":
                            obj.Start = edge.Vertexes[0].Point
                            obj.End = edge.Vertexes[-1].Point
                        elif DraftGeomUtils.geomType(edge) == "Circle":
                            c = edge.Curve.Center
                            r = edge.Curve.Radius
                            a = edge.Curve.Axis
                            ray = obj.Dimline.sub(c).projectToPlane(App.Vector(0,0,0),a)
                            if (ray.Length == 0):
                                ray = a.cross(App.Vector(1,0,0))
                                if (ray.Length == 0):
                                    ray = a.cross(App.Vector(0,1,0))
                            ray = DraftVecUtils.scaleTo(ray,r)
                            if hasattr(obj,"Diameter"):
                                if obj.Diameter:
                                    obj.Start = c.add(ray.negative())
                                    obj.End = c.add(ray)
                                else:
                                    obj.Start = c
                                    obj.End = c.add(ray)
                elif len(lsub) == 2:
                    if ("Vertex" in lsub[0]) and ("Vertex" in lsub[1]):
                        n1 = int(lsub[0][6:])-1
                        n2 = int(lsub[1][6:])-1
                        obj.Start = lobj.Shape.Vertexes[n1].Point
                        obj.End = lobj.Shape.Vertexes[n2].Point
            elif len(obj.LinkedGeometry) == 2:
                lobj1 = obj.LinkedGeometry[0][0]
                lobj2 = obj.LinkedGeometry[1][0]
                lsub1 = obj.LinkedGeometry[0][1]
                lsub2 = obj.LinkedGeometry[1][1]
                if (len(lsub1) == 1) and (len(lsub2) == 1):
                    if ("Vertex" in lsub1[0]) and ("Vertex" in lsub2[1]):
                        n1 = int(lsub1[0][6:])-1
                        n2 = int(lsub2[0][6:])-1
                        obj.Start = lobj1.Shape.Vertexes[n1].Point
                        obj.End = lobj2.Shape.Vertexes[n2].Point
        # set the distance property
        total_len = (obj.Start.sub(obj.End)).Length
        if round(obj.Distance.Value, utils.precision()) != round(total_len, utils.precision()):
            obj.Distance = total_len
        if App.GuiUp:
            if obj.ViewObject:
                obj.ViewObject.update()