
#### color utility ####
def color_rgb(r,g,b):
    '''r,g,b are intensities of r(ed), g(reen), and b(lue).
    Each value MUST be an integer in the interval [0,255]
    Returns color specifier string for the resulting color'''
    return "#%02x%02x%02x" % (r,g,b)
