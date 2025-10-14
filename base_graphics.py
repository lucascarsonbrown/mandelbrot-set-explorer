# base_graphics.py
'''An object-oriented graphics library for use with SMJExplorer.

   Originally created by JS Iwanski for the NonLinear Dynamics course
   at Dwight-Englewood School. This file is based on his design and
   implementation, with modifications for this project.

   The original library modifies and adds to the graphics.py module
   of John Zelle with added functionality for the NonLinear Dynamics
   course at Dwight-Englewood School.

   The original library was designed to make it very easy
   for novice programmers to experiment with computer graphics
   in an object-oriented fashion, as written by John Zelle for
   use with the book "Python Programming: An Introduction to
   Computer Science" (Franklin, Beedle & Associates).

   LICENSE: This is open-source software released under the
   terms of the GPL (http://www.gnu.org/licenses/gpl.html).

   PLATFORMS: The package is a wrapper around Tkinter and
   should run on any platform where Tkinter is available.
   Modified in March 2024 by JS Iwanski to break up original 
        module into DEbase_graphics.py and DEwidgets.py
   Modified June 2020 by JS Iwanski
   to add:
        Button - gives appearance of being clicked,
        and sets up SimpleButton as a subclass of Button,
        for compatability with previous versions that had
        only a SimpleButton class.

   Modified in February/March 2020 by JS Iwanski
   to add:
        IntEntry, DblEntry, SimpleButton, DropDown, Slider,
        zooming with aspect ratio maintained on DEGraphWin,
        borders and border coloring on DEGraphWin,
        titleBar on/off on DEGraphWin,
        exact screen positioning on DEGraphWin
   Originally modified in 2018 by JS Iwanski
   to add:
        DEGraphWin (eliminated original GraphWin rather 
        than extend it)
   See original graphics.py for other version information.

   Contains the following python classes:
        Transform: an internal class for 2D coordinate transforms
        GraphicsObject: generic base class for all of the drawable objects
        Point: extends GraphicsObject to create a 2D point in the plane
        BBox: extends GraphicsObject, internal class for objects represented by a bounding box
        Rectangle: extends BBox, represents a planar rectangle
        Oval: extends Bbox, represents an planar oval
        Circle: extends Oval, represents a planar circle
        Line: extends BBox, represents a planar line
        Polygon: extends GraphicsObject, represents a planar polygon by a list of Points
'''

import time, os, sys
import tkinter as tk


##########################################################################
# Module Exceptions

class GraphicsError(Exception):
    '''Generic error class for graphics module exceptions'''
    pass

OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"

##########################################################################
# global variables and functions

_root = tk.Tk()
_root.withdraw()

_update_lasttime = time.time()

def update(rate=None):
    global _update_lasttime
    if rate:
        now = time.time()
        pauseLength = 1/rate-(now-_update_lasttime)
        if pauseLength > 0:
            time.sleep(pauseLength)
            _update_lasttime = now + pauseLength
        else:
            _update_lasttime = now

    _root.update()

############################################################################
def delay(timeToDelay):
    time.sleep(timeToDelay)
############################################################################
# Graphics classes start here
class Transform:
    '''Internal class for 2-D coordinate transformations'''
    def __init__(self, w, h, xlow, ylow, xhigh, yhigh):
        # w, h are width and height of window
        # (xlow,ylow) coordinates of lower-left [raw (0,h-1)]
        # (xhigh,yhigh) coordinates of upper-right [raw (w-1,0)]
        xspan = (xhigh-xlow)
        yspan = (yhigh-ylow)
        self.xbase = xlow
        self.ybase = yhigh
        self.xscale = xspan/float(w-1)
        self.yscale = yspan/float(h-1)

    def screen(self,x,y):
        # Returns x,y in screen (actually window) coordinates
        xs = (x-self.xbase) / self.xscale
        ys = (self.ybase-y) / self.yscale
        return int(xs+0.5),int(ys+0.5)

    def world(self,xs,ys):
        # Returns xs,ys in world coordinates
        x = xs*self.xscale + self.xbase
        y = self.ybase - ys*self.yscale
        return x,y

# Default values for various item configuration options. Only a subset of
#   keys may be present in the configuration dictionary for a given item
DEFAULT_CONFIG = {"fill":"","outline":"black","width":"1","arrow":"none",
         "text":"","justify":"center","font": ("helvetica", 12, "normal")}

class GraphicsObject:
    '''Generic base class for all of the drawable objects'''
    # A subclass of GraphicsObject should override _draw and
    #   and _move methods.

    def __init__(self, options):
        # options is a list of strings indicating which options are
        # legal for this object.

        # When an object is drawn, canvas is set to the DEGraphWin(canvas)
        #    object where it is drawn and id is the TK identifier of the
        #    drawn shape.
        self.canvas = None
        self.id = None

        # config is the dictionary of configuration options for the widget.
        config = {}
        for option in options:
            config[option] = DEFAULT_CONFIG[option]
        self.config = config

    def setFill(self, color):
        '''Set interior color to color'''
        self._reconfig("fill", color)
    
    def getFill(self):
        '''Get interior color'''
        return self.config['fill']

    def setOutline(self, color):
        '''Set outline color to color'''
        self._reconfig("outline", color)

    def setWidth(self, width):
        '''Set line weight to width'''
        self._reconfig("width", width)

    def isDrawn(self):
       if self.canvas:
          return True
       else:
          return False

    def draw(self, graphwin):
        '''Draw the object in graphwin, which should be a DEGraphWin
        object.  A GraphicsObject may only be drawn into one
        window. Raises an error if attempt made to draw an object that
        is already visible.'''

        if self.canvas and not self.canvas.isClosed(): raise GraphicsError(OBJ_ALREADY_DRAWN)
        if graphwin.isClosed(): raise GraphicsError("Can't draw to closed window")
        self.canvas = graphwin
        self.id = self._draw(graphwin, self.config)
        graphwin.addItem(self)
        if graphwin.autoflush:
            _root.update()
        return self

    def undraw(self):
        '''Undraw the object (i.e. hide it). Returns silently if the
        object is not currently drawn.'''

        if not self.canvas: return
        if not self.canvas.isClosed():
            self.canvas.delete(self.id)
            self.canvas.delItem(self)
            if self.canvas.autoflush:
                _root.update()
        self.canvas = None
        self.id = None

    def move(self, dx, dy):
        '''move object dx units in x direction
           and dy units in y direction'''

        self._move(dx,dy)
        canvas = self.canvas
        if canvas and not canvas.isClosed():
            trans = canvas.trans
            if trans:
                x = dx/ trans.xscale
                y = -dy / trans.yscale
            else:
                x = dx
                y = dy
            self.canvas.move(self.id, x, y)
            if canvas.autoflush:
                _root.update()

    def _reconfig(self, option, setting):
        # Internal method for changing configuration of the object
        # Raises an error if the option does not exist in the config
        #    dictionary for this object
        if option not in self.config:
            raise GraphicsError(UNSUPPORTED_METHOD)
        options = self.config
        options[option] = setting
        if self.canvas and not self.canvas.isClosed():
            self.canvas.itemconfig(self.id, options)
            if self.canvas.autoflush:
                _root.update()


    def _draw(self, canvas, options):
        '''draws appropriate figure on canvas with options provided
           returns Tk id of item drawn'''
        pass # must override in subclass


    def _move(self, dx, dy):
        '''updates internal state of object to move it dx,dy units'''
        pass # must override in subclass

#### GEOMETRIC classes ####
class Point(GraphicsObject):
    '''2D point in the plane'''
    def __init__(self, x, y):
        GraphicsObject.__init__(self, ["outline", "fill"])
        self.setFill = self.setOutline
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return "Point({}, {})".format(self.x, self.y)

    def _draw(self, canvas, options):
        x,y = canvas.toScreen(self.x,self.y)
        return canvas.create_rectangle(x,y,x+1,y+1,options)

    def _move(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy

    def clone(self):
        other = Point(self.x,self.y)
        other.config = self.config.copy()
        return other

    def equals(self, otherPoint):
       return (self.x == otherPoint.x) and (self.y == otherPoint.y)

    def getX(self): return self.x
    def getY(self): return self.y

class _BBox(GraphicsObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.

    def __init__(self, p1, p2, options=["outline","width","fill"]):
        GraphicsObject.__init__(self, options)
        self.p1 = p1.clone()
        self.p2 = p2.clone()

    def _move(self, dx, dy):
        self.p1.x = self.p1.x + dx
        self.p1.y = self.p1.y + dy
        self.p2.x = self.p2.x + dx
        self.p2.y = self.p2.y  + dy

    def getP1(self): return self.p1.clone()

    def getP2(self): return self.p2.clone()

    def getCenter(self):
        p1 = self.p1
        p2 = self.p2
        return Point((p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0)

class Rectangle(_BBox):
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)

    def __repr__(self):
        return "Rectangle({}, {})".format(str(self.p1), str(self.p2))

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        return canvas.create_rectangle(x1,y1,x2,y2,options)

    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.config = self.config.copy()
        return other

class Oval(_BBox):
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)

    def __repr__(self):
        return "Oval({}, {})".format(str(self.p1), str(self.p2))


    def clone(self):
        other = Oval(self.p1, self.p2)
        other.config = self.config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        return canvas.create_oval(x1,y1,x2,y2,options)

class Circle(Oval):
    def __init__(self, center, radius):
        p1 = Point(center.x-radius, center.y-radius)
        p2 = Point(center.x+radius, center.y+radius)
        Oval.__init__(self, p1, p2)
        self.radius = radius

    def __repr__(self):
        return "Circle({}, {})".format(str(self.getCenter()), str(self.radius))

    def clone(self):
        other = Circle(self.getCenter(), self.radius)
        other.config = self.config.copy()
        return other

    def getRadius(self):
        return self.radius

class Line(_BBox):
    def __init__(self, p1, p2, style='solid'):
        _BBox.__init__(self, p1, p2, ["arrow","fill","width"])
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill
        self.style = style

    def __repr__(self):
        return "Line({}, {})".format(str(self.p1), str(self.p2))

    def clone(self):
        other = Line(self.p1, self.p2)
        other.config = self.config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        if self.style == 'dashed':
           return canvas.create_line(x1,y1,x2,y2,dash=(10,5), width = 2)
        elif self.style == 'dotted':
           return canvas.create_line(x1,y1,x2,y2,dash=(2,2), width = 2)
        return canvas.create_line(x1,y1,x2,y2,options)

    def getLength(self):
        return ((self.p1.x-self.p2.x)**2 + (self.p1.y-self.p2.y)**2)**0.5

    def setArrow(self, option):
        if not option in ["first","last","both","none"]:
            raise GraphicsError(BAD_OPTION)
        self._reconfig("arrow", option)

# class Polygon(GraphicsObject):
#     def __init__(self, *points):
#         # if points passed as a list, extract it
#         if len(points) == 1 and type(points[0]) == type([]):
#             points = points[0]
#         self.points = list(map(Point.clone, points))
#         GraphicsObject.__init__(self, ["outline", "width", "fill"])

#     def __repr__(self):
#         return "Polygon"+str(tuple(p for p in self.points))

#     def clone(self):
#         other = Polygon(*self.points)
#         other.config = self.config.copy()
#         return other

#     def getPoints(self):
#         return list(map(Point.clone, self.points))

#     def _move(self, dx, dy):
#         for p in self.points:
#             p.move(dx,dy)

#     def _draw(self, canvas, options):
#         args = [canvas]
#         for p in self.points:
#             x,y = canvas.toScreen(p.x,p.y)
#             args.append(x)
#             args.append(y)
#         args.append(options)
#         return DEGraphWin.create_polygon(*args)

# MacOS fix 1
update()
