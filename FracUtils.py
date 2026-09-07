# utilities for drawing fractal objects and
# for generally exploring fractals

from base_graphics import *
from widgets import *
from utils import *
from polygon import Polygon
import math as m
import random

# P0 is the starting Point of the segment
# theta is the angle (in degrees) that the segment is inclined from P0
# L is the desired length of the segment
# thickness is the thickness of the line (integer > 0)
# color is the color of the segment
# win is the DEGraphWin upon which we will draw the segment
def drawLine(win, P0, theta, L, thickness=1, color="black"):
    dx = L * m.cos(m.radians(theta))
    dy = L * m.sin(m.radians(theta))
    line = Line(P0, Point(P0.getX() + dx, P0.getY() + dy))
    line.setFill(color)
    line.setWidth(thickness)
    line.draw(win)
    P0.move(dx, dy)
    return line

# draws a Koch curve of order level
def drawKochCurve(win, level, P0, L, lineList, thetaIncline=0, thetaKC=60, color='black', thickness=1):
    if level == 0:
        lineList.append(drawLine(win, P0, thetaIncline, L, thickness, color))
    else:
        newL = L * (1/(2+2*m.cos(m.radians(thetaKC))))
        drawKochCurve(win, level-1, P0, newL, lineList, thetaIncline, thetaKC, color, thickness)
        drawKochCurve(win, level-1, P0, newL, lineList, thetaIncline+thetaKC, thetaKC, color, thickness)
        drawKochCurve(win, level-1, P0, newL, lineList, thetaIncline-thetaKC, thetaKC, color, thickness)
        drawKochCurve(win, level-1, P0, newL, lineList, thetaIncline, thetaKC, color, thickness)

# draws a Koch polygon of order level
def drawKochPolygon(win, sides, level, P0, L, lineList, thetaIncline=0, thetaKC=60, color='black', thickness=1):
    nextAngle = ((sides-2)*180)/sides
    for i in range(sides):
        if i == 0:
            drawKochCurve(win, level, P0, L, lineList, thetaIncline, thetaKC, color, thickness)
        else:
            drawKochCurve(win, level, P0, L, lineList, thetaIncline + i*(180 + nextAngle), thetaKC, color, thickness)


# draws a Koch curve of order n with a randomization factor
def drawRandomizedKochCurve(win, level, P0, L, lineList, degreeOfDifference=15, thetaIncline=0, thetaKC=60, color='black', thickness=1):
    if level == 0:
        lineList.append(drawLine(win, P0, thetaIncline, L, thickness, color))
    else:
        newL = L * (1 / (2 + 2 * m.cos(m.radians(thetaKC))))
        randomThetaKC = thetaKC + random.uniform(-degreeOfDifference, degreeOfDifference)  
        drawRandomizedKochCurve(win, level - 1, P0, newL, lineList, degreeOfDifference, thetaIncline, randomThetaKC, color, thickness)
        drawRandomizedKochCurve(win, level - 1, P0, newL, lineList, degreeOfDifference, thetaIncline + randomThetaKC, randomThetaKC, color, thickness)
        drawRandomizedKochCurve(win, level - 1, P0, newL, lineList, degreeOfDifference, thetaIncline - randomThetaKC, randomThetaKC, color, thickness)
        drawRandomizedKochCurve(win, level - 1, P0, newL, lineList, degreeOfDifference, thetaIncline, randomThetaKC, color, thickness)

# draws a Koch polygon of order level with a randomization factor
def drawRandomizedKochPolygon(win, sides, level, P0, L, lineList, degreeOfDifference=15, thetaIncline=0, thetaKC=60, color='black', thickness=1):
    nextAngle = ((sides-2)*180)/sides
    for i in range(sides):
        if i == 0:
            drawRandomizedKochCurve(win, level, P0, L, lineList, degreeOfDifference, thetaIncline, thetaKC, color, thickness)
        else:
            drawRandomizedKochCurve(win, level, P0, L, lineList, degreeOfDifference, thetaIncline + i*(180 + nextAngle), thetaKC, color, thickness)

def drawColoredKochCurve(win, level, max_level, P0, L, lineList, thetaIncline=0, thetaKC=60, thickness=1):
    ratio = (max_level - level) / max_level  
    red = int(255 * ratio)
    blue = int(255 * (1 - ratio))
    color = color_rgb(red, 0, blue)  

    # Draw the line segment at every recursive call:
    lineList.append(drawLine(win, P0, thetaIncline, L, thickness, color))

    if level > 0:
        newL = L * (1 / (2 + 2 * m.cos(m.radians(thetaKC))))
        
        # Recursive calls: Ideally, you'll also update P0 to the new start point for each segment
        drawColoredKochCurve(win, level-1, max_level, P0, newL, lineList, thetaIncline, thetaKC, thickness)
        drawColoredKochCurve(win, level-1, max_level, P0, newL, lineList, thetaIncline+thetaKC, thetaKC, thickness)
        drawColoredKochCurve(win, level-1, max_level, P0, newL, lineList, thetaIncline-thetaKC, thetaKC, thickness)
        drawColoredKochCurve(win, level-1, max_level, P0, newL, lineList, thetaIncline, thetaKC, thickness)
