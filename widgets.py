# widgets.py
'''An object-oriented graphics widget library for use with SMJExplorer.

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
        module into base_graphics.py and widgets.py
   Latest version modified June 2020 by JS Iwanski
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
        
   Originally modified in 2018 by JS Iwanski to add:
        DEGraphWin (eliminated original GraphWin rather than extend it)
   See original graphics.py for other version information.

   Contains the following python classes:
        DEGraphWin: extends tk.Canvas, a full-function graphics standalone window
        Text: extends GraphicsObject, a box for putting text in a window
        Entry: extends GraphicsObject, a general entry object for string input
        IntEntry: extends Entry, for whole number input
        DblEntry: extends Entry, for floating-point entry
        Button: a clickable button for graphics apps
        SimpleButton: extends Button, button with more primitive behavior
        DropDown: extends GraphicsObject, for a drop-down selection box
        Slider: extends GraphicsObject, a slider for selections
        Image: extends GraphicsObject, for inserting images into apps
        _is_number(s): determines whether string s is numeric
        
'''

import time, os, sys
from base_graphics import *
from utils import *

try:  # import as appropriate for 2.x vs. 3.x
   import tkinter as tk
except:
   import Tkinter as tk

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

# for zooming on DEGraphWin, in or out
ZOOM_IN = "in"
ZOOM_OUT = "out"

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
class DEGraphWin(tk.Canvas):
    '''A DEGraphWin is a toplevel window for displaying graphics. It
       stores its current custom coordinates, default coordinates,
       size in pixels (width,height), two forms of coordinate axes,
       and various display characteristics of those axes.'''

    def __init__(self, title = "Dwight-Englewood graphics window",
    	         defCoords=[-10,-10,10,10], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 600, height = 600,
                 offsets=[0,0], autoflush = False,
                 hasTitlebar = True,
                 hThickness=2, hBGColor="blue",
                 borderWidth=0):

        assert type(title) == type(""), "Title must be a string"
        self.master = tk.Toplevel(_root)
        self.master.protocol("WM_DELETE_WINDOW", self.close)
        tk.Canvas.__init__(self, self.master, width=width, height=height,
                           highlightthickness=hThickness, highlightbackground=hBGColor,
                           bd=borderWidth)
        self.master.title(title)

        # if does not have the title bar, no controls on it, and window
        # is not resizeable nor is it movable
        if hasTitlebar == False:
            self.master.overrideredirect(True) # removes title bar
            #self.wm_attributes('-type', 'splash')

        # implements the width, height, and where the window opens with respect
        # to the top-left corner of the screen, as dictated by offsets
        #   offsets[0]: how far from left edge of screen (in pixels)
        #   offsets[1]: how far from top edge of screen (in pixels)
        self.master.geometry('%dx%d+%d+%d' % (width, height,
                                              offsets[0], offsets[1]))
        self.pack()

        # margin = [h,v], where
        #          h : left and right margins as percentage of total width
        #          v : top and bottom margins as percentage of total height
        # (in other words, h and v should be between 0 and 0.5)

        # axisType:
        #     0 - classic x-y axes
        #     1 - 'box' axis around window

        self.axisType = axisType
        self.axisStyle = axisStyle
        self.axesDrawn = False
        self.axisColor = axisColor
        self.margin = margin

        # zoomBox is a Rectangle that will be drawn when
        # a zoom IN is requested, and then undrawn.
        self.zoomBox = Rectangle(Point(0,0),Point(0,0))
        self.zoomBoxColor = 'black'

        # default coordinates that we can return to
        self.defaultCoords = defCoords

        # default background color is black
        self.foreground = "black"

        self.title = title
        self.height = int(height)
        self.width = int(width)
        self.master.resizable(0,0)
        self.items = []
        self.mouseX = None
        self.mouseY = None
        self.bind("<Button-1>", self._onClick)
        self.bind_all("<Key>", self._onKey)
        self.autoflush = autoflush
        self._mouseCallback = None
        self.trans = None
        self.closed = False

        self.currentCoords = []
        self.setCoords(defCoords[0],defCoords[1],defCoords[2],defCoords[3])

        # axes will store two sets of axes:
        #    0 - classic x-y axes (2)
        #    1 - box axes around edges (4)
        self.axes = []
        self.updateAxes(self.axisType,self.axisStyle)
        self.currentAxes = self.axes[self.axisType]

        self.gridLines = []
        self.gridDrawn = False

        self.master.lift()
        self.lastKey = ""
        if autoflush: _root.update()

    def __repr__(self):
        if self.isClosed():
            return "<Closed DEGraphWin>"
        else:
            return "DEGraphWin('{}', {}, {})".format(self.master.title(),
                                             self.getWidth(),
                                             self.getHeight())

    def __str__(self):
        return repr(self)

    def __checkOpen(self):
        if self.closed:
            raise GraphicsError("window is closed")

    def _onKey(self, evnt):
        self.lastKey = evnt.keysym

    def clear(self):
        '''clears drawn elements on the DEGraphWin'''
        self.delete("all")
        self.redraw()

    def setTitle(self,newTitle):
       '''change the title to newTitle'''
       self.master.title(newTitle)

    def grid(self, dx = 1, dy = 1, color = 'black'):
        if self.gridDrawn:
            for line in self.gridLines:
                line.undraw()
            self.gridLines = []
        else:
            xm = self.currentCoords[0]
            xM = self.currentCoords[2]
            ym = self.currentCoords[1]
            yM = self.currentCoords[3]

            x = xm
            while x < xM:
                L = Line(Point(x,ym),Point(x,yM))
                L.setOutline(color)
                L.draw(self)
                self.gridLines.append(L)
                x += dx
            
            y = ym
            while y < yM:
                L = Line(Point(xm,y),Point(xM,y))
                L.setOutline(color)
                L.draw(self)
                self.gridLines.append(L)
                y += dy
        self.gridDrawn = not self.gridDrawn

    def setBackground(self, color):
        '''Set background color of the window'''
        self.__checkOpen()
        self.config(bg=color)
        self.__autoflush()

    def close(self):
        '''Close the window'''
        if self.closed: return
        self.closed = True
        self.master.destroy()
        self.__autoflush()

    def isClosed(self):
        return self.closed

    def isOpen(self):
        return not self.closed

    def __autoflush(self):
        if self.autoflush:
            _root.update()

    def plot(self, x, y, color="black"):
        '''Set pixel (x,y) to the given color'''
        self.__checkOpen()
        xs,ys = self.toScreen(x,y)
        self.create_line(xs,ys,xs+1,ys, fill=color)
        self.__autoflush()

    def plotPixel(self, x, y, color="black"):
        '''Set pixel raw (ind. of window coordinates) pixel (x,y) to color'''
        self.__checkOpen()
        self.create_line(x,y,x+1,y, fill=color)
        self.__autoflush()

    def flush(self):
        '''Update drawing to the window'''
        self.__checkOpen()
        self.update_idletasks()

    def getMouse(self):
        '''Wait for mouse click and return Point object from the click'''
        self.update()      # flush any prior clicks
        self.mouseX = None
        self.mouseY = None
        while self.mouseX == None or self.mouseY == None:
            self.update()
            if self.isClosed(): raise GraphicsError("getMouse in closed window")
            time.sleep(.1) # give up thread
        x,y = self.toWorld(self.mouseX, self.mouseY)
        self.mouseX = None
        self.mouseY = None
        return Point(x,y)

    def checkMouse(self, delay = 0.1):
        '''Return last mouse click or None if mouse has
        not been clicked since last call'''
        if self.isClosed():
            raise GraphicsError("checkMouse in closed window")
        self.update()
        if self.mouseX != None and self.mouseY != None:
            x,y = self.toWorld(self.mouseX, self.mouseY)
            self.mouseX = None
            self.mouseY = None
            time.sleep(delay)
            return Point(x,y)
        else:
            time.sleep(delay)
            return None


    def getKey(self):
        '''Wait for user to press a key and return it as a string'''
        self.lastKey = ""
        while self.lastKey == "":
            self.update()
            if self.isClosed(): raise GraphicsError("getKey in closed window")
            time.sleep(.1) # give up thread

        key = self.lastKey
        self.lastKey = ""
        return key

    def checkKey(self):
        '''Return last key pressed or None if no key pressed since last call'''
        if self.isClosed():
            raise GraphicsError("checkKey in closed window")
        self.update()
        key = self.lastKey
        self.lastKey = ""
        return key

    def getHeight(self):
        '''Return the height of the window'''
        return self.height

    def getWidth(self):
        '''Return the width of the window'''
        return self.width

    def toScreen(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.screen(x,y)
        else:
            return x,y

    def toWorld(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.world(x,y)
        else:
            return x,y

    def setMouseHandler(self, func):
        self._mouseCallback = func

    def _onClick(self, e):
        self.mouseX = e.x
        self.mouseY = e.y
        if self._mouseCallback:
            self._mouseCallback(Point(e.x, e.y))

    def addItem(self, item):
        self.items.append(item)

    def delItem(self, item):
        self.items.remove(item)

    def redraw(self):
        for item in self.items[:]:
            item.undraw()
            item.draw(self)
        self.update()

    def toggleAxes(self):
        '''toggles axes from shown to hidden and vice-versa'''
        if self.axesDrawn: # already drawn, so undraw
            for i in range(len(self.currentAxes)):
                self.currentAxes[i].undraw()
        else: # not drawn, so draw 'em
            for i in range(len(self.currentAxes)):
                self.currentAxes[i].setFill(self.axisColor)
                self.currentAxes[i].draw(self)
        self.axesDrawn = not self.axesDrawn

    # axisStyle can be 'dashed', 'dotted', or 'solid'
    def setAxisStyle(self, axisStyle):
        self.axisStyle = 'solid'
        if axisStyle in ['solid','dashed','dotted']:
            self.axisStyle = axisStyle
        self.updateAxes(self.axisType, self.axisStyle)

    # axisType can be
    #   0 - standard axes
    #   1 - square axes
    def setAxisType(self, axisType):
        self.axisType = 0
        if axisType in [0,1]:
            self.axisType = axisType
        self.updateAxes(self.axisType, self.axisStyle)

    def updateAxes(self, axType, axisStyle):
        '''updates coordinate axes for current scaling'''
        # 0. get rid of old axes
        # first undraw 'em (if drawn)
        if self.axesDrawn:
           for i in range(len(self.currentAxes)):
                self.currentAxes[i].undraw()
        # then empty the list
        while len(self.axes) > 0:
            waste = self.axes.pop()

        # 1. store necessary variables
        xm = self.currentCoords[0]
        xM = self.currentCoords[2]
        ym = self.currentCoords[1]
        yM = self.currentCoords[3]

        # 2. take care of classic axes
        xAxis = Line(Point(xm,0),Point(xM,0),axisStyle)
        yAxis = Line(Point(0,ym),Point(0,yM),axisStyle)
        axes_classic = [xAxis,yAxis]
        self.axes.append(axes_classic)

        # 3. take care of box axes
        hTop = Line(Point(xm,yM - 0.1*(yM-ym)),Point(xM,yM - 0.1*(yM-ym)),axisStyle)
        hBot = Line(Point(xm,ym + 0.1*(yM-ym)),Point(xM,ym + 0.1*(yM-ym)),axisStyle)
        vLef = Line(Point(xm + 0.1*(xM-xm),ym),Point(xm + 0.1*(xM-xm),yM),axisStyle)
        vRgt = Line(Point(xM - 0.1*(xM-xm),ym),Point(xM - 0.1*(xM-xm),yM),axisStyle)
        axes_box = [hTop,hBot,vLef,vRgt]
        self.axes.append(axes_box)

        #4. update axis style
        self.axisType = axType
        self.currentAxes = self.axes[self.axisType]

        for i in range(len(self.currentAxes)):
            self.currentAxes[i].setFill(self.axisColor)

        #5. redraw axes if necessary
        if self.axesDrawn:
           for i in range(len(self.currentAxes)):
                self.currentAxes[i].draw(self)

    def setDefaultCoords(self, newDefault):
        self.defaultCoords = newDefault

    def setCoords(self,x1,y1,x2,y2):
        # force x1 < x2 and y1 < y2
        if x1 > x2:
            temp = x1
            x1 = x2
            x2 = temp
        if y1 > y2:
            temp = y1
            y1 = y2
            y2 = temp

        width  = abs(x2 - x1)
        height = abs(y2 - y1)

        self.currentCoords=[x1,y1,x2,y2]

        # calculate new x,y values incorporating margins
        newx1 = x1 - self.margin[0] * width
        newx2 = x2 + self.margin[0] * width
        newy1 = y1 - self.margin[1] * height
        newy2 = y2 + self.margin[1] * height

        # call parent setCoords
        #self.setCoords(newx1,newy1,newx2,newy2)
        self.trans = Transform(self.width, self.height, newx1, newy1, newx2, newy2)
        self.redraw()

    def zoom(self, whichWay = ZOOM_IN, keepRatio = False, color = "black"):
        '''permits zooming IN or zooming OUT (back to default)'''
        self.zoomBoxColor = color
        
        if whichWay == ZOOM_IN:
            if not keepRatio:
                #print("Click on " + self.title + " to input one corner of the zoom box")
                pt1 = self.getMouse()
                #print("Click on " + self.title + " to input the opposite corner of the zoom box")
                pt2 = self.getMouse()

                # if the second point results in a degenerate area,
                # must re-select the second point.
                while (pt1.getX() == pt2.getX()) or (pt1.getY() == pt2.getY()):
                    #print("Click on " + self.title + " to input the opposite corner of the zoom box")
                    pt2 = self.getMouse()

                # form the zoomBox - shows the zoom area graphically to user
                self.zoomBox = Rectangle(pt1,pt2)
                self.zoomBox.setOutline(self.zoomBoxColor)
                self.zoomBox.draw(self)
                self.update()
                self.getMouse()

                # ask if they are sure they want this zoom
                #doyouwanttozoom = input("Is this the zoom you want? (type 'y' or 'n')")
                # while not(doyouwanttozoom == 'y' or doyouwanttozoom == 'n'):
                #     doyouwanttozoom = input("Please type 'y' or 'n': ")
                doyouwanttozoom = 'y'
                if doyouwanttozoom == 'y':
                    # erase the zoomBox
                    self.zoomBox.undraw()
                    # erase the window
                    self.clear()
                    x1 = min(pt1.x,pt2.x)
                    x2 = max(pt1.x,pt2.x)
                    y1 = min(pt1.y,pt2.y)
                    y2 = max(pt1.y,pt2.y)
                    self.setCoords(x1,y1,x2,y2)
                    # print("Zoomed in to [" + '{:03.4f}'.format(self.currentCoords[0])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[1])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[2])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[3]) + "]")
                else:
                    self.zoomBox.undraw()
            else: # we will maintain the original aspect ratio
                # will use the zoom width only, and set height accordingly
                pt1 = self.getMouse()
                temp = self.getMouse()
                while pt1.getX() == temp.getX():
                    temp = self.getMouse()
                # AR is width:height, so dx/dy = width/height
                # or dy = dx (height/width)
                x1 = min(pt1.x,temp.x)
                x2 = max(pt1.x,temp.x)
                tempy1 = pt1.y
                ratio = self.height/self.width
                if temp.y > pt1.y: # go UP
                    tempy2 = tempy1 + (x2-x1)*ratio
                else:              # go DOWN
                    tempy2 = tempy1 - (x2-x1)*ratio
                y1 = min(tempy1,tempy2)
                y2 = max(tempy1,tempy2)
                pt1 = Point(x1,y1)
                pt2 = Point(x2,y2)
                # form the zoomBox - shows the zoom area graphically to user
                self.zoomBox = Rectangle(pt1,pt2)
                self.zoomBox.setOutline(self.zoomBoxColor)
                self.zoomBox.draw(self)
                self.update()
                self.getMouse()
                self.zoomBox.undraw()

                # ask if they are sure they want this zoom
                #doyouwanttozoom = input("Is this the zoom you want? (type 'y' or 'n')")
                # while not(doyouwanttozoom == 'y' or doyouwanttozoom == 'n'):
                #     doyouwanttozoom = input("Please type 'y' or 'n': ")
                doyouwanttozoom = 'y'
                if doyouwanttozoom == 'y':
                    # erase the zoomBox
                    self.zoomBox.undraw()
                    # erase the window
                    self.clear()
                    x1 = min(pt1.x,pt2.x)
                    x2 = max(pt1.x,pt2.x)
                    y1 = min(pt1.y,pt2.y)
                    y2 = max(pt1.y,pt2.y)
                    self.setCoords(x1,y1,x2,y2)
                    # print("Zoomed in to [" + '{:03.4f}'.format(self.currentCoords[0])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[1])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[2])
                    #       + "," + '{:03.4f}'.format(self.currentCoords[3]) + "]")
                else:
                    self.zoomBox.undraw()
        elif whichWay == ZOOM_OUT:
            # zooms back to defaultCoords
            # print("Zooming OUT to [" + '{:03.4f}'.format(self.defaultCoords[0])
            #           + "," + '{:03.4f}'.format(self.defaultCoords[1])
            #           + "," + '{:03.4f}'.format(self.defaultCoords[2])
            #           + "," + '{:03.4f}'.format(self.defaultCoords[3]) + "]")
            x1 = self.defaultCoords[0]
            y1 = self.defaultCoords[1]
            x2 = self.defaultCoords[2]
            y2 = self.defaultCoords[3]

            # erase the window
            self.clear()
            self.setCoords(x1,y1,x2,y2)
            self.update()

#----------------------------------------------------

class Text(GraphicsObject):
    '''a label widget for fixed text'''
    def __init__(self, p, text):
        GraphicsObject.__init__(self, ["justify","fill","text","font"])
        self.setText(text)
        self.anchor = p.clone()
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill

    def __repr__(self):
        return "Text({}, '{}')".format(self.anchor, self.getText())

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        return canvas.create_text(x,y,options)

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def clone(self):
        other = Text(self.anchor, self.config['text'])
        other.config = self.config.copy()
        return other

    def setText(self,text):
        self._reconfig("text", text)

    def getText(self):
        return self.config["text"]

    def getAnchor(self):
        return self.anchor.clone()

    def setFace(self, face):
        if face in ['helvetica','arial','courier','times roman','verdana','comic sans','papyrus']:
            f,s,b = self.config['font']
            self._reconfig("font",(face,s,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 60:
            f,s,b = self.config['font']
            self._reconfig("font", (f,size,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            f,s,b = self.config['font']
            self._reconfig("font", (f,s,style))
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.setFill(color)

class Entry(GraphicsObject):
    '''widget for getting text input from a user'''
    def __init__(self, center, width):
        GraphicsObject.__init__(self, [])
        self.anchor = center.clone()
        #print self.anchor
        self.width = width
        self.text = tk.StringVar(_root)
        self.text.set("")
        self.fill = "gray"
        self.color = "black"
        self.font = DEFAULT_CONFIG['font']
        self.entry = None

    def __repr__(self):
        return "Entry({}, {})".format(self.anchor, self.width)

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Entry(frm,
                              width=self.width,
                              textvariable=self.text,
                              bg = self.fill,
                              fg = self.color,
                              font=self.font,
                              justify='center')
        self.entry.pack()
        #self.setFill(self.fill)
        self.entry.focus_set()
        return canvas.create_window(x,y,window=frm)

    def getText(self):
        return self.text.get()

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def getAnchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Entry(self.anchor, self.width)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def setText(self, t):
        self.text.set(t)

    def setFill(self, color):
        self.fill = color
        if self.entry:
            self.entry.config(bg=color)

    def _setFontComponent(self, which, value):
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            self.entry.config(font=self.font)

    def setFace(self, face):
        if face in ['helvetica','arial','courier','times roman']:
            self._setFontComponent(0, face)
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 36:
            self._setFontComponent(1,size)
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            self._setFontComponent(2,style)
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.color=color
        if self.entry:
            self.entry.config(fg=color)

class IntEntry(Entry):
    '''extension of Entry to get integer input in a desired range'''
    def __init__(self, center, width, span = [0,10],
                       colors = ['gray','black'],
                       errorColors = ['red','white']):
        Entry.__init__(self, center,width)

        self.setFill(colors[0])
        self.setTextColor(colors[1])
        self.colors = colors
        self.errorcolors = errorColors
        self.min = min(int(span[0]),int(span[1]))
        self.max = max(int(span[0]),int(span[1]))
        self.setDefault(int((self.max + self.min)/2))

    def __repr__(self):
        return "IntEntry({}, {} to {})".format(self.anchor, self.min, self.max)

    def setDefault(self, val):
        '''updates the default value of the entry field'''
        if self.min <= val <= self.max:
            self.defaultValue = int(val)

    def getValue(self):
        # first get the text from the entry object
        text = self.getText()
        # if the text is NOT a number, then
        # return the default value
        if not _is_number(text):
            self.setFill(self.errorcolors[0])
            self.setTextColor(self.errorcolors[1])
            self.setText(int(self.defaultValue))
            return int(self.defaultValue)
        else:
            # otherwise, the text IS numeric, so
            # check first that it is in the range of
            # permitted values
            tempVal = int(float(text))
            if self.min <= tempVal <= self.max:
                self.setFill(self.colors[0])
                self.setTextColor(self.colors[1])
                self.setText(tempVal)
                return int(tempVal)
            else:
                # if it is NOT in the permitted range of values,
                # then return the default value
                self.setFill(self.errorcolors[0])
                self.setTextColor(self.errorcolors[1])
                self.setText(int(self.defaultValue))
                return int(self.defaultValue)

class DblEntry(Entry):
    '''extension of Entry to get floating point input in a desired range'''
    def __init__(self, center, width, span = [0,1],
                       colors = ['gray','black'],
                       errorColors = ['red','white']):
        Entry.__init__(self, center,width)

        self.setFill(colors[0])
        self.setTextColor(colors[1])
        self.colors = colors
        self.errorcolors = errorColors
        self.min = min(span[0],span[1])
        self.max = max(span[0],span[1])
        self.defaultValue = (self.max + self.min)/2.0

    def __repr__(self):
        return "DblEntry({}, {} to {})".format(self.anchor, self.min, self.max)

    def setDefault(self, val):
        '''updates the default value of the entry field'''
        if self.min <= val <= self.max:
            self.defaultValue = val

    def getValue(self):
        # first get the text from the entry object
        text = self.getText()
        # if the text is NOT a number, then
        # return the default value
        if not _is_number(text):
            self.setFill(self.errorcolors[0])
            self.setTextColor(self.errorcolors[1])
            self.setText(self.defaultValue)
            return self.defaultValue
        else:
            # otherwise, the text IS numeric, so
            # check first that it is in the range of
            # permitted values
            tempVal = float(text)
            if self.min <= tempVal <= self.max:
                self.setFill(self.colors[0])
                self.setTextColor(self.colors[1])
                self.setText(tempVal)
                return tempVal
            else:
                # if it is NOT in the permitted range of values,
                # then return the default value
                self.setFill(self.errorcolors[0])
                self.setTextColor(self.errorcolors[1])
                self.setText(self.defaultValue)
                return self.defaultValue
            
#### A button class that has appearance of being clicked ####
class Button:

    '''A button is a labeled rectangle in a window.
    It is enabled/disabled with the activate()/deactivate()
    methods. The clicked(point) method returns true if the
    button is active while being clicked. Designer can set
    various properties, including:
        > button's color, edge color, and text color
        > button's CLICKED color, edge color, and text color
        > the time delay (seconds) for the click appearance
        > the label (caption) on the button
        > the width of the button's edge
        > the font face and size of the label
        > the position of the top-left corner of the button
        > the button's width and height (in custom coordinates)
        > the window in which the button will be placed'''

    # define the button constructor
    def __init__(self, win, topLeft, width, height,
                 edgeWidth = 2, label = 'button caption',
                 buttonColors = ['lightgray','black','black'],
                 clickedColors = ['white','red','black'],
                 font=('courier',18), timeDelay = 0.25):
        # buttonColors contains [button BG color, button EDGE color, textcolor]

        self.parent = win

        self.topleft = topLeft
        w,h = width/2.0, height/2.0
        x,y = topLeft.getX() + w, topLeft.getY() - h

        center = topLeft.clone()
        center.move(w,-h)

        self.xmax, self.xmin = x+w, x-w
        self.ymax, self.ymin = y+h, y-h

        # points defining opposing corners of button
        p1 = Point(self.xmin,self.ymin)
        p2 = Point(self.xmax, self.ymax)

        # define the button rectangle
        self.backcolor = buttonColors[0]
        self.backcolorClicked = clickedColors[0]
        self.rect = Rectangle(p1, p2)
        self.rect.setFill(self.backcolor)
        self.edgewidth = edgeWidth
        self.edgecolor = buttonColors[1]
        self.edgecolorClicked = clickedColors[1]
        self.rect.setOutline(self.edgecolor)
        self.rect.setWidth(self.edgewidth)

        # define the button caption
        self.forecolor = buttonColors[2]
        self.forecolorClicked = clickedColors[2]
        self.caption = Text(center, label)
        self.caption.setSize(font[1])
        self.caption.setFace(font[0])
        self.caption.setFill(self.forecolor)

        self.timeDelay = timeDelay

        # draw the button
        self.rect.draw(win)
        self.caption.draw(win)


    def __repr__(self):
        '''basic representation of a simple button'''
        return "Button({})".format(self.topleft)

    def clicked(self, clickPoint):
        '''Returns true if button is clicked on while active,
           and false otherwise'''
        if (self.active and
                self.xmin <= clickPoint.getX() <= self.xmax and
                self.ymin <= clickPoint.getY() <= self.ymax):
            self.appearClicked(self.timeDelay)
            return True
        else:
            return False

    def getCaption(self):
        '''Returns the caption of the button'''
        return self.caption.getText()

    def setCaption(self, newCaption):
        '''Sets the button caption to newCaption'''
        self.caption.setText(newCaption)

    def changeLabelColorTo(self, newColor):
        '''modifies the saved caption color and
           changes the caption color field'''
        self.forecolor = newColor
        self.caption.setFill(newColor)

    def setLabelColor(self,newColor):
        '''changes the caption color to newColor'''
        self.caption.setFill(newColor)

    def changeButtonColorTo(self, newColor):
        '''changes the button BG color and
           changes the BG color field'''
        self.backcolor = newColor
        self.rect.setFill(newColor)

    def setButtonColor(self, newColor):
        '''Sets the background color to newColor'''
        self.rect.setFill(newColor)

    def changeEdgeColorTo(self, newColor):
        '''changes the edge color and
           changes the edge color field'''
        self.edgecolor = newColor
        self.rect.setOutline(newColor)

    def setEdgeColor(self, newColor):
        '''Sets the edge color of the button to newColor'''
        self.rect.setOutline(newColor)

    def appearClicked(self, timeDelay):
        '''gives button appearance of being clicked'''
        self.setEdgeColor(self.edgecolorClicked)
        self.setButtonColor(self.backcolorClicked)
        self.setLabelColor(self.forecolorClicked)
        self.parent.update()
        delay(timeDelay)
        self.setEdgeColor(self.edgecolor)
        self.setButtonColor(self.backcolor)
        self.setLabelColor(self.forecolor)
        self.parent.update()

    def draw(self,win):
        '''draws this simple button on window win'''
        self.rect.draw(win)
        self.caption.draw(win)

    def undraw(self):
        '''undraws (hides) this simple button'''
        self.rect.undraw()
        self.caption.undraw()

    def activate(self):
        '''enables this button'''
        self.setEdgeColor(self.edgecolor)
        self.setButtonColor(self.backcolor)
        self.setLabelColor(self.forecolor)
        self.active = True

    def deactivate(self):
        '''disables this button'''
        self.setEdgeColor(self.edgecolorClicked)
        self.setButtonColor(self.backcolorClicked)
        self.setLabelColor(self.forecolorClicked)
        self.rect.setWidth(1)
        self.active = False

class SimpleButton(Button):
    '''just like a Button but no click appearance'''

    def __init__(self, win, topLeft, width, height,
                 edgeWidth = 2, label = 'button caption',
                 buttonColors = ['lightgray','blue','black'],
                 font=('courier',18)):
        Button.__init__(self, win, topLeft, width, height,
                 edgeWidth=edgeWidth, label=label, buttonColors=buttonColors, font=font)

    def __repr__(self):
        '''basic representation of a simple button'''
        return "SimpleButton({})".format(self.topleft)

    def clicked(self, clickPoint):
        '''Returns true if button is clicked on while active,
           and false otherwise'''
        return self.active and self.xmin <= clickPoint.getX() <= self.xmax and self.ymin <= clickPoint.getY() <= self.ymax

class DropDown(GraphicsObject):
    def __init__(self, topLeft,choices=[],font=('courier',18),bg='black'):
        GraphicsObject.__init__(self, [])
        self.anchor = topLeft.clone()
        self.text = tk.StringVar(_root)
        self.text.set("")
        self.fill = "gray"
        self.color = "black"
        self.bgColor=bg
        self.font=font
        self.choices = choices
        self.menu = None

    def __repr__(self):
        return "DropDown({}, {})".format(self.anchor, self.width)

    def _draw(self, canvas, options):
        frm = tk.Frame(canvas.master)
        self.text.set(self.choices[0])
        self.menu = tk.OptionMenu(frm,self.text,*self.choices)

        # force the OptionMenu to have a width
        # commensurate with its longest element
        self.width = max([len(choice) for choice in self.choices])
        self.menu.config(width=self.width)

        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)

        self.menu.config(font=self.font)
        self.menu.config(bg=self.bgColor)
        menu = self.menu.nametowidget(self.menu.menuname)
        menu.configure(font=self.font)
        self.menu.pack()
        #self.setFill(self.fill)
        self.menu.focus_set()
        return canvas.create_window(x,y,window=frm)

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def setFill(self, color):
        self.fill = color
        if self.menu:
            self.menu.config(bg=color)

    def setTextColor(self, color):
        self.color=color
        if self.menu:
            self.menu.config(fg=color)

    def getChoice(self):
        return self.text.get()

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            self._setFontComponent(2,style)
        else:
            raise GraphicsError(BAD_OPTION)

class Slider(GraphicsObject):
    def __init__(self, p, length, height, initVal,
                 min = 0, max = 10,
                 font = ('courier',18),
                 label = "", orient = "H",
                 resolution = 1, tickinterval = 0,
                 bg='black',fg='black', trColor = 'gray'):
        GraphicsObject.__init__(self, [])

        self.anchor = p.clone()
        self.fill = "gray"
        self.fg = fg
        self.min = min
        self.trColor = trColor
        self.label = label
        self.font = font
        self.res = resolution
        self.tick = tickinterval

        # take care of orientation: vertical or horizontal
        if orient == "V":
            self.orient = tk.VERTICAL
            self.width = length
            self.height = height
        else:
            self.orient = tk.HORIZONTAL
            self.width = height
            self.height = length
        self.max = max
        self.bgColor=bg
        self.slider = None
        self.initialValue = initVal

    def __repr__(self):
        return "Slider({}, {})".format(self.anchor, self.width)

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        frm = tk.Frame(canvas.master)

        self.slider = tk.Scale(frm, from_=self.min, to=self.max,
                               width = self.width,length = self.height,
                               borderwidth=1,fg=self.fg,bg=self.bgColor,
                               troughcolor = self.trColor,
                               label = self.label,
                               font = self.font,
                               sliderlength = 10,
                               tickinterval = self.tick,
                               resolution = self.res,
                               orient = self.orient)
        self.slider.set(self.initialValue)
        self.slider.pack()
        #self.setFill(self.fill)
        self.slider.focus_set()
        return canvas.create_window(x,y,window=frm)

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def update_scale(self,new_max):
        self.slider.configure(to=new_max)

    def setFill(self, color):
        self.fill = color
        if self.slider:
            self.slider.config(bg=color)

    def setTextColor(self, color):
        self.color=color
        if self.slider:
            self.slider.config(fg=color)

    def getValue(self):
        return self.slider.get()
    
    def setValue(self, value):
        self.slider.set(value)

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            self._setFontComponent(2,style)
        else:
            raise GraphicsError(BAD_OPTION)

class Image(GraphicsObject):
    '''GraphicsObject designed to hold an image (pixelmap)'''
    idCount = 0
    imageCache = {} # tk photoimages go here to avoid GC while drawn

    def __init__(self, p, *pixmap):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        self.imageId = Image.idCount
        Image.idCount = Image.idCount + 1
        if len(pixmap) == 1: # file name provided
            self.img = tk.PhotoImage(file=pixmap[0], master=_root)
        else: # width and height provided
            width, height = pixmap
            self.img = tk.PhotoImage(master=_root, width=width, height=height)

    def __repr__(self):
        return "Image({}, {}, {})".format(self.anchor, self.getWidth(), self.getHeight())

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        self.imageCache[self.imageId] = self.img # save a reference
        return canvas.create_image(x,y,image=self.img)

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def undraw(self):
        try:
            del self.imageCache[self.imageId]  # allow gc of tk photoimage
        except KeyError:
            pass
        GraphicsObject.undraw(self)

    def getAnchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Image(Point(0,0), 0, 0)
        other.img = self.img.copy()
        other.anchor = self.anchor.clone()
        other.config = self.config.copy()
        return other

    def getWidth(self):
        """Returns the width of the image in pixels"""
        return self.img.width()

    def getHeight(self):
        """Returns the height of the image in pixels"""
        return self.img.height()

    def getPixel(self, x, y):
        '''Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256)'''

        value = self.img.get(x,y)
        if type(value) ==  type(0):
            return [value, value, value]
        elif type(value) == type((0,0,0)):
            return list(value)
        else:
            return list(map(int, value.split()))

    def setPixel(self, x, y, color):
        '''Sets pixel (x,y) to the given color'''
        self.img.put("{" + color +"}", (x, y))

    def save(self, filename):
        '''Saves the pixmap image to filename.
        The format for the save image is determined
        from the filname extension.'''

        path, name = os.path.split(filename)
        ext = name.split(".")[-1]
        self.img.write( filename, format=ext)

# function to determine whether a string s is numeric
def _is_number(stringS):
    try:
        float(stringS)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(stringS)
        return True
    except (TypeError, ValueError):
        pass

    return False
