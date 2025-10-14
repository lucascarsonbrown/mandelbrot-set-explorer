"""
SMJExplorer.py - Super Mandelbrot and Julia Set Explorer

A graphical application for exploring and visualizing the Mandelbrot and Julia sets.
This program provides an interactive interface for:
    - Visualizing the Mandelbrot set with various coloring schemes
    - Exploring Julia sets for different complex parameter values
    - Zooming in and out of both sets
    - Computing periods of points in the Mandelbrot set
    - Escape time coloring for beautiful fractal visualization

Author: Lucas Brown
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

import sys
sys.path.append("../util")

from widgets import *
from base_graphics import *
from utils import *
from random import random
import webbrowser as wb
import math as m

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================

# Color palette - all colors pulled from the background title image for visual consistency
Colors = {
    "purple": color_rgb(41, 20, 57),           # Deep purple for backgrounds
    "magenta": color_rgb(142, 69, 102),        # Magenta for fractal rendering
    "orange": color_rgb(255, 159, 64),         # Orange accent color
    "blue": color_rgb(39, 81, 128),            # Blue for UI elements
    "white": color_rgb(243, 240, 220),         # Off-white for backgrounds
    "red": color_rgb(188, 79, 63),             # Red accent color
    "deeper white": color_rgb(227, 226, 185)   # Slightly darker white variant
}

# Global dictionaries to manage UI components
windows = {}         # Stores all window objects (Title, Mandelbrot Set, Julia Set, Control Panel, Extra)
labels = {}          # Stores all text labels and visual elements
buttons = {}         # Stores all button objects for user interaction
GraphingObjects = {} # Stores all interactive graphing elements (sliders, entries)

# Current complex parameter value for Julia set exploration
c = complex(0, 0)

# ==============================================================================
# MATHEMATICAL FUNCTIONS - Core Fractal Computation
# ==============================================================================

def f(z, c):
    """
    The quadratic map function: f(z) = z^2 + c

    This is the fundamental iteration function for both Mandelbrot and Julia sets.

    Parameters:
        z (complex): The current complex number value
        c (complex): The complex parameter

    Returns:
        complex: The result of z^2 + c
    """
    return z*z + c

def finv(z, c):
    """
    The inverse function of f: f^-1(z) = sqrt(z - c)

    Randomly selects between the positive and negative square root to
    explore both branches of the inverse map. Used for drawing Julia sets
    via the Inverse Iteration Method.

    Parameters:
        z (complex): The current complex number value
        c (complex): The complex parameter

    Returns:
        complex: One of the two square roots of (z - c), chosen randomly
    """
    val = (z-c)**0.5
    return val if random() < 0.5 else (-val)

def getPeriod(c, iterates=100000):
    """
    Computes the period of a point c in the Mandelbrot set.

    For points inside the Mandelbrot set, the orbit eventually becomes periodic.
    This function detects when a value repeats and returns the period length.

    Parameters:
        c (complex): The complex parameter to test
        iterates (int): Maximum number of iterations to check (default: 100000)

    Returns:
        int: The period of the orbit, or -1 if the point is not in the Mandelbrot set
             or if no period is found within the iteration limit
    """
    z = 0
    pastValues = {}
    if inMbrot(c):
        for i in range(iterates):
            z = f(z, c)
            if z in pastValues:
                return i - pastValues[z]
            pastValues[z] = i
    return -1

# ==============================================================================
# JULIA SET FUNCTIONS
# ==============================================================================

def inFilledJulia(z0, c=complex(0,0), maxIterations=100, R=2.0):
    """
    Tests if a point z0 is in the filled Julia set for parameter c.

    The filled Julia set consists of points whose orbit under iteration
    of f(z) = z^2 + c remains bounded.

    Parameters:
        z0 (complex): The initial point to test
        c (complex): The Julia set parameter (default: 0+0i)
        maxIterations (int): Maximum iterations before considering bounded (default: 100)
        R (float): Escape radius (default: 2.0)

    Returns:
        tuple: (bool, int) - (True if in filled Julia set, iteration count)
    """
    iterations = 0
    while iterations < maxIterations and abs(z0) < R:
        z0 = f(z0, c)
        iterations += 1
    return iterations == maxIterations, iterations

def inJuliaBoundary(z0, c=complex(0, 0), maxIterations=100, R=2.0, epsilon=1e-5):
    """
    Tests if a point z0 is on the boundary of the Julia set for parameter c.

    The Julia set boundary consists of points that exhibit chaotic behavior,
    neither clearly diverging nor stabilizing.

    Parameters:
        z0 (complex): The initial point to test
        c (complex): The Julia set parameter (default: 0+0i)
        maxIterations (int): Maximum iterations to check (default: 100)
        R (float): Escape radius (default: 2.0)
        epsilon (float): Threshold for detecting stable points (default: 1e-5)

    Returns:
        tuple: (bool, int) - (True if on Julia boundary, iteration count)
    """
    z = z0
    iterations = 0

    while iterations < maxIterations:
        # Check for divergence
        if abs(z) > R:
            return False, iterations  # Clearly diverging, not on the boundary

        z_next = z**2 + c
        # Check if the point is sensitive to small changes in z (chaotic behavior)
        if abs(z_next - z) < epsilon:
            return False, iterations  # Stable, not on the boundary

        z = z_next
        iterations += 1

    # If the point neither diverges nor stabilizes within maxIterations, it is on the boundary
    return True, iterations

def drawJulia(win, c, transient=10000, iterations=25000):
    """
    Draws the Julia set using the Inverse Iteration Method.

    This method starts with a random point and iteratively applies the inverse
    function finv() to trace out the Julia set boundary.

    Parameters:
        win (DEGraphWin): The window to draw in
        c (complex): The Julia set parameter
        transient (int): Number of initial iterations to discard (default: 10000)
        iterations (int): Number of points to plot (default: 25000)
    """
    # 1. Pick a random, complex number in the plane, z0
    z0 = complex(1000*random(), 1000*random())
    # 2. Iterate the transient to get onto the attractor
    for i in range(transient):
        z0 = finv(z0,c)
    # 3. Iterate and plot points on the Julia set
    for i in range(iterations):
        win.plot(z0.real, z0.imag, Colors['magenta'])
        z0 = finv(z0,c)
    win.update()

def drawFilledJulia(win, c, maxIterates=100, R=2.0, numSweeps=4, resolution=1):
    """
    Draws the filled Julia set by testing each point in the viewing window.

    Points in the filled Julia set are colored, points outside are left white.
    Uses a sweep pattern for progressive rendering.

    Parameters:
        win (DEGraphWin): The window to draw in
        c (complex): The Julia set parameter
        maxIterates (int): Maximum iterations for escape test (default: 100)
        R (float): Escape radius (default: 2.0)
        numSweeps (int): Number of interlaced sweeps for rendering (default: 4)
        resolution (int): Step size multiplier for faster rendering (default: 1)
    """
    rmin, imin, rmax, imax = win.currentCoords
    stepsize = (rmax-rmin)/(win.width)

    for sweep in range(numSweeps):
        r = rmin + stepsize*sweep
        while r < rmax:
            i = imin
            while i < imax:
                z0 = complex(r, i)
                if inFilledJulia(z0, c, maxIterates, R)[0]:
                    win.plot(r, i, Colors['magenta'])
                i += resolution * stepsize
            r += numSweeps * stepsize
        win.update()

def drawFilledJulia_escape(win, c, maxIterates=100, R=2.0, numSweeps=1, resolution=1):
    """
    Draws the Julia set with escape time coloring.

    Colors points based on how quickly they escape to infinity, creating
    beautiful gradient effects around the fractal boundary.

    Parameters:
        win (DEGraphWin): The window to draw in
        c (complex): The Julia set parameter
        maxIterates (int): Maximum iterations for escape test (default: 100)
        R (float): Escape radius (default: 2.0)
        numSweeps (int): Number of interlaced sweeps for rendering (default: 1)
        resolution (int): Step size multiplier for faster rendering (default: 1)
    """
    rmin, imin, rmax, imax = win.currentCoords
    stepsize = (rmax-rmin)/(win.width)

    for sweep in range(numSweeps):
        r = rmin + stepsize*sweep
        while r < rmax:
            i = imin
            while i < imax:
                z0 = complex(r, i)
                result = inFilledJulia(z0, c, maxIterates, R)
                if not result[0]:
                    # Compute a color based on escape time
                    myColor = compute_logarithmic_colorJS(result[1])
                    win.plot(r, i, myColor)
                i += resolution * stepsize
            r += numSweeps * stepsize
        win.update()

# ==============================================================================
# COLOR COMPUTATION FUNCTIONS
# ==============================================================================

def compute_logarithmic_colorMB(value):
    """
    Computes a color based on the period value for Mandelbrot set visualization.

    Uses logarithmic scaling to map period values to a red-blue gradient.

    Parameters:
        value (int): The period value to color

    Returns:
        str: RGB color string for graphics library
    """
    if value == -1:
        return color_rgb(0, 0, 255)

    value = max(0.0001, value)

    # Logarithmic scaling for better visual distribution
    scaled_value = m.log(1 + value) / m.log(101)

    scaled_value = min(1, max(0, scaled_value))

    # Interpolate between red and blue
    r = int(255 * (1 - scaled_value))
    b = int(255 * scaled_value)

    return color_rgb(r, 0, b)

def compute_logarithmic_colorJS(value):
    """
    Computes a color based on escape time for Julia set visualization.

    Uses logarithmic scaling to create smooth color gradients from white to blue.

    Parameters:
        value (int): The escape time value to color

    Returns:
        str: RGB color string for graphics library
    """
    small_color = (243, 240, 220)  # Off-white for fast escape
    large_color = (39, 81, 128)    # Blue for slow escape

    if value == -1:
        return color_rgb(0, 0, 255)

    value = max(0.0001, value)

    # Logarithmic scaling for smooth gradients
    scaled_value = m.log(1 + value) / m.log(101)
    scaled_value = min(1, max(0, scaled_value))

    # Interpolate between the two colors
    r = int((1 - scaled_value) * small_color[0] + scaled_value * large_color[0])
    g = int((1 - scaled_value) * small_color[1] + scaled_value * large_color[1])
    b = int((1 - scaled_value) * small_color[2] + scaled_value * large_color[2])

    return color_rgb(r, g, b)

# ==============================================================================
# MANDELBROT SET FUNCTIONS
# ==============================================================================

def inMbrot(c, maxIterations=100, R=2.0):
    """
    Tests if a point c is in the Mandelbrot set.

    The Mandelbrot set consists of complex values c for which the orbit
    of z = 0 under iteration of f(z) = z^2 + c remains bounded.

    Parameters:
        c (complex): The point to test
        maxIterations (int): Maximum iterations before considering bounded (default: 100)
        R (float): Escape radius (default: 2.0)

    Returns:
        bool: True if c is in the Mandelbrot set, False otherwise
    """
    z0 = complex(0,0)
    iterations = 0
    while iterations < maxIterations and abs(z0) < R:
        z0 = f(z0, c)
        iterations += 1
    return iterations == maxIterations

def drawMbrot(win, maxIterations=100, color='red', numSweeps=4, resolution=1):
    """
    Draws the Mandelbrot set in a single color.

    Tests each point in the viewing window and colors it if it's in the set.

    Parameters:
        win (DEGraphWin): The window to draw in
        maxIterations (int): Maximum iterations for escape test (default: 100)
        color (str): Color to use for the set (default: 'red')
        numSweeps (int): Number of interlaced sweeps for rendering (default: 4)
        resolution (int): Step size multiplier for faster rendering (default: 1)
    """
    rmin, imin, rmax, imax = win.currentCoords
    stepsize = (rmax - rmin) / (win.width*2)
    for sweep in range(numSweeps):
        r = rmin + stepsize*sweep
        while r < rmax:
            i = imin
            while i < imax:
                c = complex(r, i)
                if inMbrot(c, maxIterations):
                    win.plot(r, i, color)
                i += stepsize * resolution
            r += stepsize * numSweeps
        win.update()

def drawPeriodColorMbrot(win, maxIterations=100):
    """
    Draws the Mandelbrot set with period-based coloring.

    Different periodic regions of the Mandelbrot set are colored differently
    based on their period, revealing the beautiful internal structure.

    Parameters:
        win (DEGraphWin): The window to draw in
        maxIterations (int): Maximum iterations for escape test (default: 100)
    """
    rmin, imin, rmax, imax = win.currentCoords
    stepsize = (rmax - rmin) / (win.width*2)
    r = rmin
    while r < rmax:
        i = imin
        while i < imax:
            c = complex(r, i)
            if inMbrot(c, maxIterations):
                # Compute color based on period (using fewer iterates for performance)
                win.plot(r, i, compute_logarithmic_colorMB(getPeriod(c, iterates=1000)))
            i += stepsize
        r += stepsize
    win.update()

# ==============================================================================
# WINDOW INITIALIZATION
# ==============================================================================

def initializeWindows():
    """
    Initializes all windows for the application.

    Creates and configures five windows:
        1. Title Window - Displays the application title and background
        2. Mandelbrot Set Window - For visualizing the Mandelbrot set
        3. Julia Set Window - For visualizing Julia sets
        4. Control Panel Window - Contains all UI controls
        5. Extra Window - Hidden utility window
    """
    global windows

    # Window positioning offsets
    xOffest = 50
    yOffset = 50

    # ===== TITLE WINDOW =====
    # Creates the top banner with application title and background image
    winTitle = DEGraphWin(title = "Lucas' Logistic Explorer",
    	         defCoords = [0, 0, 10, 10], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 1300, height = 150,
                 offsets=[xOffest,yOffset], autoflush = False,
                 hasTitlebar = False,
                 hThickness=2, hBGColor=Colors["blue"],
                 borderWidth=0)
    windows['Title'] = winTitle
    winTitle.setBackground(Colors['white'])

    # Background image for visual appeal
    background = Image(Point(4,3.4), "SMJExplorerBackgroundResized.png")
    background.draw(windows['Title'])

    # Title text with shadow effect
    tsLabel = Text(p = Point(5, 5), text="Lucas' Super Mandelbrot Explorer")
    tsLabel.setTextColor("black")
    tsLabel.setSize(60)
    tsLabel.draw(windows['Title'])
    tsLabelBehind = Text(p = Point(5.03, 5.3), text="Lucas' Super Mandelbrot Explorer")
    tsLabelBehind.setTextColor(Colors["white"])
    tsLabelBehind.setSize(60)
    tsLabelBehind.draw(windows['Title'])

    labels['Background Photo'] = background
    labels['Title Black'] = tsLabelBehind
    labels['Title'] = tsLabel

    # ===== MANDELBROT SET WINDOW =====
    # Left visualization window for the Mandelbrot set
    winMBS = DEGraphWin(title = "Mandelbrot Set",
    	         defCoords = [-3, -3, 3, 3], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 650, height = 650,
                 offsets=[xOffest,yOffset+winTitle.height], autoflush = False,
                 hasTitlebar = False,
                 hThickness=2, hBGColor=Colors['blue'],
                 borderWidth=0)
    windows['Mandelbrot Set'] = winMBS
    winMBS.setBackground(Colors['white'])

    # ===== JULIA SET WINDOW =====
    # Right visualization window for Julia sets
    winJS = DEGraphWin(title = "Julia Set",
    	         defCoords = [-3, -3, 3, 3], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 650, height = 650,
                 offsets=[xOffest+winMBS.width,yOffset+winTitle.height], autoflush = False,
                 hasTitlebar = False,
                 hThickness=2, hBGColor=Colors['blue'],
                 borderWidth=0)
    windows['Julia Set'] = winJS
    winJS.setBackground(Colors['white'])

    # ===== CONTROL PANEL WINDOW =====
    # Right sidebar containing all interactive controls
    winCP = DEGraphWin(title = "Julia Set",
    	         defCoords = [0, 0, 10, 10], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 300, height = 800,
                 offsets=[xOffest+(winTitle.width),yOffset], autoflush = False,
                 hasTitlebar = False,
                 hThickness=2, hBGColor=Colors['blue'],
                 borderWidth=0)
    windows['Control Panel'] = winCP
    winCP.setBackground(Colors['white'])

    # ===== EXTRA WINDOW =====
    # Hidden utility window for future use
    winExtra = DEGraphWin(title = "",
    	         defCoords = [0, 0, 10, 10], margin = [0,0],
                 axisType = 0, axisColor = 'black', axisStyle = 'solid',
                 width = 5, height = 5,
                 offsets=[10000,10000], autoflush = False,
                 hasTitlebar = True,
                 hThickness=2, hBGColor=Colors['blue'],
                 borderWidth=0)
    windows['Extra'] = winExtra

# ==============================================================================
# BUTTON AND UI ELEMENT INITIALIZATION
# ==============================================================================

def initializeButtons():
    """
    Initializes all buttons, labels, and interactive UI elements.

    Creates the complete control panel interface including:
        - Action buttons (Exit, Help, Clear)
        - C value input and display
        - Period computation button
        - Zoom controls for both windows
        - Plotting mode buttons
        - Iteration slider
    """
    global c

    # ===== PRIMARY ACTION BUTTONS =====

    # Exit button - Closes the application
    btnExit = Button(windows["Control Panel"], topLeft = Point(0.8, 0.8), width = 2.5, height = 0.55,
                 edgeWidth = 2, label = 'Exit',
                 buttonColors = [Colors['blue'],'black','black'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Exit'] = btnExit
    btnExit.activate()

    # Help button - Opens custom GPT assistant for help
    btnHelp = Button(windows["Control Panel"], topLeft = Point(3.75, 0.8), width = 2.5, height = 0.55,
                 edgeWidth = 2, label = 'Help',
                 buttonColors = [Colors['blue'],'black','black'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Help'] = btnHelp
    btnHelp.activate()

    # Clear button - Clears both visualization windows
    btnClear = Button(windows["Control Panel"], topLeft = Point(6.7, 0.8), width = 2.5, height = 0.55,
                 edgeWidth = 2, label = 'Clear',
                 buttonColors = [Colors['blue'],'black','black'],
                 clickedColors = ['darkgray','black','black'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Clear'] = btnClear
    btnClear.activate()

    # ===== ITERATION CONTROL =====

    # Background label for iteration slider
    iteratesLabel = Rectangle(Point(0.5, 8.3), Point(9.5, 7.3))
    iteratesLabel.setFill(Colors['purple'])
    iteratesLabel.draw(windows['Control Panel'])
    labels['Iterate Label'] = iteratesLabel

    # Slider for controlling iteration count
    entryIterates = Slider(p = Point(5,7.8), length = 250, height = 10, initVal = 200,
                 min = 0, max = 500,
                 font = ('courier',12),
                 label = "Iterations", orient = "H",
                 resolution = 1, tickinterval = 250,
                 bg='lightgray',fg='black', trColor = 'gray')
    GraphingObjects['Iterates Slider'] = entryIterates
    entryIterates.draw(windows['Control Panel'])

    # ===== C VALUE INPUT AND DISPLAY =====

    # Entry field for real part of c
    entryR = DblEntry(Point(3.5,9.3), 7, span = [-4,4],
                       colors = ['gray','black'],
                       errorColors = ['red','white'])
    GraphingObjects['R Entry'] = entryR
    entryR.draw(windows['Control Panel'])

    # Entry field for imaginary part of c
    entryI = DblEntry(Point(6.5,9.3), 7, span = [-4,4],
                       colors = ['gray','black'],
                       errorColors = ['red','white'])
    GraphingObjects['I Entry'] = entryI
    entryI.draw(windows['Control Panel'])

    # Background label for c value display
    cLabel = Rectangle(Point(2, 9.9), Point(8, 9))
    cLabel.setFill(Colors['purple'])
    cLabel.draw(windows['Control Panel'])
    labels['C Label'] = cLabel

    # Text display showing current c value
    currentCValue = Text(p = Point(5, 9.7), text=f"c = {round(c.real, 4)} + {round(c.imag, 4)}i")
    currentCValue.setTextColor("white")
    currentCValue.setSize(15)
    currentCValue.draw(windows['Control Panel'])
    labels['Current C Value'] = currentCValue

    # Text display for period information
    currentPeriod = Text(p = Point(5, 5.8), text="")
    currentPeriod.setTextColor("black")
    currentPeriod.setSize(15)
    currentPeriod.draw(windows['Control Panel'])
    labels['Current Period'] = currentPeriod

    # ===== C VALUE CONTROL BUTTONS =====

    # Button to get c value by clicking on Mandelbrot set
    btnGetJSValue = Button(windows["Control Panel"], topLeft = Point(3.75, 8.9), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'Get C\nValue',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','black'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Get Julia Set Value'] = btnGetJSValue
    btnGetJSValue.activate()

    # Button to compute period of current c value
    btnGetPeriod = Button(windows["Control Panel"], topLeft = Point(7, 8.9), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'Get\nPeriod',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Get Period'] = btnGetPeriod
    btnGetPeriod.activate()

    # Button to manually set c value from entry fields
    btnSetCValue = Button(windows["Control Panel"], topLeft = Point(0.5, 8.9), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'Set C\nValue',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Set C Value'] = btnSetCValue
    btnSetCValue.activate()

    # ===== MANDELBROT ZOOM CONTROLS =====

    # Background label for Mandelbrot zoom controls
    zoomMBLabel = Rectangle(Point(1.5, 1.8), Point(4.5, 1))
    zoomMBLabel.setFill(Colors['purple'])
    zoomMBLabel.draw(windows['Control Panel'])
    labels['Zomm MB Background'] = zoomMBLabel

    # Label text for Mandelbrot controls
    MBLabel = Text(p = Point(3, 1.6), text="Mandelbrot")
    MBLabel.setTextColor("white")
    MBLabel.setSize(15)
    MBLabel.draw(windows['Control Panel'])
    labels['MB Label'] = MBLabel

    # Zoom in button for Mandelbrot window
    btnZoomMB = Button(windows["Control Panel"], topLeft = Point(1.8, 1.4), width = 1, height = 0.3,
                 edgeWidth = 2, label = '+',
                 buttonColors = [Colors['blue'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Zoom on MB'] = btnZoomMB
    btnZoomMB.activate()

    # Zoom out button for Mandelbrot window
    btnZoomOutMB = Button(windows["Control Panel"], topLeft = Point(3.2, 1.4), width = 1, height = 0.3,
                 edgeWidth = 2, label = '-',
                 buttonColors = [Colors['blue'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Zoom out MB'] = btnZoomOutMB
    btnZoomOutMB.activate()

    # ===== JULIA SET ZOOM CONTROLS =====

    # Background label for Julia zoom controls
    zoomJSLabel = Rectangle(Point(5.5, 1.8), Point(8.5, 1))
    zoomJSLabel.setFill(Colors['purple'])
    zoomJSLabel.draw(windows['Control Panel'])
    labels['Zomm JS Background'] = zoomJSLabel

    # Label text for Julia controls
    JSLabel = Text(p = Point(7, 1.6), text="Julia")
    JSLabel.setTextColor("white")
    JSLabel.setSize(15)
    JSLabel.draw(windows['Control Panel'])
    labels['JS Label'] = JSLabel

    # Zoom in button for Julia window
    btnZoomJS = Button(windows["Control Panel"], topLeft = Point(5.8, 1.4), width = 1, height = 0.3,
                 edgeWidth = 2, label = '+',
                 buttonColors = [Colors['blue'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Zoom on JS'] = btnZoomJS
    btnZoomJS.activate()

    # Zoom out button for Julia window
    btnZoomOutJS = Button(windows["Control Panel"], topLeft = Point(7.2, 1.4), width = 1, height = 0.3,
                 edgeWidth = 2, label = '-',
                 buttonColors = [Colors['blue'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Zoom out JS'] = btnZoomOutJS
    btnZoomOutJS.activate()

    # ===== PLOTTING MODE BUTTONS =====

    # Button to plot standard Mandelbrot set
    btnPlotMB = Button(windows["Control Panel"], topLeft = Point(2, 6.6), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'MB',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Plot MB'] = btnPlotMB
    btnPlotMB.activate()

    # Button to plot Julia set (inverse iteration method)
    btnPlotJS = Button(windows["Control Panel"], topLeft = Point(0.5, 7.2), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'JS',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Plot JS'] = btnPlotJS
    btnPlotJS.activate()

    # Button to plot filled Julia set
    btnPlotFilledJS = Button(windows["Control Panel"], topLeft = Point(3.75, 7.2), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'FJS',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Plot Filled JS'] = btnPlotFilledJS
    btnPlotFilledJS.activate()

    # Button to plot Julia set with escape time coloring
    btnPlotJSEscape = Button(windows["Control Panel"], topLeft = Point(7, 7.2), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'JSE',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Plot JS Escape'] = btnPlotJSEscape
    btnPlotJSEscape.activate()

    # Button to plot period-colored Mandelbrot set
    btnPlotPCMB = Button(windows["Control Panel"], topLeft = Point(5.5, 6.6), width = 2.5, height = 0.5,
                 edgeWidth = 2, label = 'PCMB',
                 buttonColors = [Colors['purple'],'black','white'],
                 clickedColors = ['darkgray','black','white'],
                 font=('courier',18), timeDelay = 0.1)
    buttons['Plot Period Color MB'] = btnPlotPCMB
    btnPlotPCMB.activate()

# ==============================================================================
# WINDOW MANAGEMENT
# ==============================================================================

def closeWindows():
    """
    Closes all windows and cleans up UI elements.

    Undraws all labels and closes all windows in the application.
    """
    global windows
    for label in labels.values():
        label.undraw()
    for win in windows.values():
        win.close()

# ==============================================================================
# BUTTON CALLBACK FUNCTIONS
# ==============================================================================

def exitButton():
    """
    Callback for Exit button.
    Closes all windows and terminates the application.
    """
    closeWindows()

def helpButton():
    """
    Callback for Help button.
    Opens a web browser to the custom GPT help assistant.
    """
    wb.open("https://chatgpt.com/g/g-67881b892c888191bb57e0c41ab70da4-lucas-super-mandelbrot-helper")

def clearButton():
    """
    Callback for Clear button.
    Clears both visualization windows and resets the period display.
    """
    windows['Mandelbrot Set'].clear()
    windows['Julia Set'].clear()
    labels['Current Period'].setText("")

def getJSValueButton():
    """
    Callback for Get C Value button.
    Allows user to click on the Mandelbrot set window to select a c value
    for Julia set exploration.
    """
    global c
    clickpoint = windows['Mandelbrot Set'].getMouse()
    c = complex(clickpoint.x, clickpoint.y)
    labels['Current C Value'].setText(f"c = {round(c.real, 4)} + ({round(c.imag, 4)})i")

def setCValue():
    """
    Callback for Set C Value button.
    Sets the c value from the manual entry fields for real and imaginary parts.
    """
    global c
    r = GraphingObjects['R Entry'].getValue()
    i = GraphingObjects['I Entry'].getValue()
    c = complex(r, i)
    labels['Current C Value'].setText(f"c = {round(c.real, 4)} + ({round(c.imag, 4)})i")

def zoomMBrot(colored):
    """
    Zooms in on the Mandelbrot set window and redraws.

    Parameters:
        colored (bool): If True, redraw with period coloring; if False, use standard coloring
    """
    windows['Mandelbrot Set'].zoom()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    if colored:
        drawPeriodColorMbrot(windows['Mandelbrot Set'], iterates)
    else:
        drawMbrot(windows['Mandelbrot Set'], iterates, Colors['magenta'])

def zoomOutMBrot(colored):
    """
    Zooms out on the Mandelbrot set window to default view and redraws.

    Parameters:
        colored (bool): If True, redraw with period coloring; if False, use standard coloring
    """
    windows['Mandelbrot Set'].zoom('out')
    iterates = GraphingObjects['Iterates Slider'].getValue()
    if colored:
        drawPeriodColorMbrot(windows['Mandelbrot Set'], iterates)
    else:
        drawMbrot(windows['Mandelbrot Set'], iterates, Colors['magenta'])

def zoomJulia(c, filled, escape):
    """
    Zooms in on the Julia set window and redraws.

    Parameters:
        c (complex): The Julia set parameter
        filled (bool): If True, draw filled Julia set
        escape (bool): If True, draw with escape time coloring
    """
    windows['Julia Set'].zoom()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    if filled:
        drawFilledJulia(windows['Julia Set'], c, iterates)
    elif escape:
        drawFilledJulia_escape(windows['Julia Set'], c, iterates)
    else:
        drawJulia(windows['Julia Set'], c, iterates)

def zoomOutJulia(c, filled, escape):
    """
    Zooms out on the Julia set window to default view and redraws.

    Parameters:
        c (complex): The Julia set parameter
        filled (bool): If True, draw filled Julia set
        escape (bool): If True, draw with escape time coloring
    """
    windows['Julia Set'].zoom('out')
    iterates = GraphingObjects['Iterates Slider'].getValue()
    if filled:
        drawFilledJulia(windows['Julia Set'], c, iterates)
    elif escape:
        drawFilledJulia_escape(windows['Julia Set'], c, iterates)
    else:
        drawJulia(windows['Julia Set'], c, iterates)

def getPeriodButton():
    """
    Callback for Get Period button.
    Computes and displays the period of the current c value.
    """
    global c
    period = getPeriod(c)
    labels['Current Period'].setText(f"Current Period: {period}")

def plotJuliaSet():
    """
    Callback for JS button.
    Plots the Julia set using the inverse iteration method.
    """
    global c
    windows['Julia Set'].clear()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawJulia(windows['Julia Set'], c, iterates)

def plotMbrot():
    """
    Callback for MB button.
    Plots the standard Mandelbrot set.
    """
    windows['Mandelbrot Set'].clear()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawMbrot(windows['Mandelbrot Set'], iterates, Colors['magenta'])

def plotFilledJulia():
    """
    Callback for FJS button.
    Plots the filled Julia set.
    """
    global c
    windows['Julia Set'].clear()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawFilledJulia(windows['Julia Set'], c, iterates)

def plotPeriodColorMbrot():
    """
    Callback for PCMB button.
    Plots the Mandelbrot set with period-based coloring.
    """
    windows['Mandelbrot Set'].clear()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawPeriodColorMbrot(windows['Mandelbrot Set'], iterates)

def plotJSEscape():
    """
    Callback for JSE button.
    Plots the Julia set with escape time coloring.
    """
    global c
    windows['Julia Set'].clear()
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawFilledJulia_escape(windows['Julia Set'], c, iterates)

# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """
    Main application loop.

    Initializes the UI, draws initial fractals, and enters the event loop
    to handle user interactions with buttons and controls.
    """
    global c

    # State variables to track which visualization mode is active
    ColoredMB = False      # Tracks if Mandelbrot is using period coloring
    filledJulia = False    # Tracks if Julia set is using filled mode
    juliaEscape = False    # Tracks if Julia set is using escape time coloring

    # Initialize the user interface
    initializeWindows()
    initializeButtons()

    # Draw initial visualizations
    iterates = GraphingObjects['Iterates Slider'].getValue()
    drawMbrot(windows['Mandelbrot Set'], iterates, Colors['magenta'])
    drawJulia(windows['Julia Set'], complex(0,0))

    # Main event loop - processes button clicks
    while True:
        clickPoint = windows["Control Panel"].getMouse()

        # Check which button was clicked and call appropriate handler
        if buttons['Exit'].clicked(clickPoint):
            exitButton()
            break
        elif buttons['Help'].clicked(clickPoint):
            helpButton()
        elif buttons['Clear'].clicked(clickPoint):
            clearButton()
        elif buttons['Get Julia Set Value'].clicked(clickPoint):
            getJSValueButton()
        elif buttons['Get Period'].clicked(clickPoint):
            getPeriodButton()
        elif buttons['Zoom on JS'].clicked(clickPoint):
            zoomJulia(c, filledJulia, juliaEscape)
        elif buttons['Zoom out JS'].clicked(clickPoint):
            zoomOutJulia(c, filledJulia, juliaEscape)
        elif buttons['Zoom on MB'].clicked(clickPoint):
            zoomMBrot(ColoredMB)
        elif buttons['Zoom out MB'].clicked(clickPoint):
            zoomOutMBrot(ColoredMB)
        elif buttons['Plot MB'].clicked(clickPoint):
            plotMbrot()
            ColoredMB = False
        elif buttons['Plot JS'].clicked(clickPoint):
            plotJuliaSet()
        elif buttons['Plot Filled JS'].clicked(clickPoint):
            filledJulia = True
            plotFilledJulia()
        elif buttons['Plot JS Escape'].clicked(clickPoint):
            juliaEscape = True
            filledJulia = False
            plotJSEscape()
        elif buttons['Plot Period Color MB'].clicked(clickPoint):
            plotPeriodColorMbrot()
            ColoredMB = True
        elif buttons['Set C Value'].clicked(clickPoint):
            setCValue()

# ==============================================================================
# PROGRAM ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()
