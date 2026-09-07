"""Renders docs/gallery.png — the README hero image.

This is a documentation tool, not part of the application. It reimplements the
same escape-time iteration the explorer uses (z -> z^2 + c) with NumPy so the
figure renders in a couple of seconds. The explorer itself is pure stdlib and
draws through Tkinter; nothing here is imported by it.

    pip install numpy matplotlib && python3 docs/render_gallery.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

MAXIT, ESCAPE = 400, 2.0

def escape_counts(re_lo, re_hi, im_lo, im_hi, px, c=None):
    """Smooth escape time on a grid. c=None -> Mandelbrot (z0=0, c varies).

    Returns a float array; points that never escape are NaN so the interior
    of the set can be painted as a solid colour rather than as a band.
    """
    re = np.linspace(re_lo, re_hi, px)
    im = np.linspace(im_lo, im_hi, int(px * (im_hi - im_lo) / (re_hi - re_lo)))
    Z0 = re[None, :] + 1j * im[:, None]
    if c is None:
        C, Z = Z0, np.zeros_like(Z0)
    else:
        C, Z = np.full(Z0.shape, c), Z0.copy()
    out = np.full(Z.shape, np.nan)
    live = np.ones(Z.shape, dtype=bool)
    for n in range(MAXIT):
        Z[live] = Z[live] ** 2 + C[live]
        gone = live & (np.abs(Z) > ESCAPE)
        # normalised iteration count: n + 1 - log(log|z|)/log 2, which removes
        # the visible banding a raw integer count produces
        az = np.abs(Z[gone])
        out[gone] = n + 1 - np.log(np.log(az)) / np.log(2)
        live &= ~gone
        if not live.any():
            break
    return out

BG, FG, ACC = "#1b2817", "#faf4e6", "#a48854"
cmap = LinearSegmentedColormap.from_list(
    "forest", ["#101a0e", "#2b3819", "#576d3b", "#a48854", "#f1f5fc", "#a48854"])
cmap.set_bad("#0a0f08")  # interior of the set: never escapes

# c values chosen to sit inside, on, and outside the set boundary
# Verified against the iteration before use: the first two c are in M, the
# third is not, which is exactly the distinction the bottom row illustrates.
JULIA = [(-1.0 + 0.0j,    "c in M — connected (basilica)"),
         (-0.12 + 0.75j,  "c in M — connected (Douady rabbit)"),
         (0.40 + 0.35j,   "c outside M — Cantor dust")]

fig = plt.figure(figsize=(11, 8.6))
fig.patch.set_facecolor(BG)
gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1], hspace=0.22, wspace=0.06,
                      left=0.04, right=0.96, top=0.90, bottom=0.09)

ax = fig.add_subplot(gs[0, :])
m = escape_counts(-2.2, 0.8, -1.25, 1.25, 1600)
ax.imshow(np.sqrt(m), cmap=cmap, extent=[-2.2, 0.8, -1.25, 1.25], origin="lower")
ax.set_xticks([]); ax.set_yticks([])
ax.set_title("The Mandelbrot set — which c keep the orbit of 0 bounded",
             color=FG, fontsize=12, pad=8)
for i, (c, _) in enumerate(JULIA):
    ax.plot(c.real, c.imag, "o", ms=8, mfc="none", mec="#ff6b4a", mew=1.8)
    ax.annotate(str(i + 1), (c.real, c.imag), color="#ff6b4a", fontsize=10,
                xytext=(7, 5), textcoords="offset points")

for i, (c, label) in enumerate(JULIA):
    a = fig.add_subplot(gs[1, i])
    j = escape_counts(-1.6, 1.6, -1.2, 1.2, 800, c=c)
    a.imshow(np.sqrt(j), cmap=cmap, extent=[-1.6, 1.6, -1.2, 1.2], origin="lower")
    a.set_xticks([]); a.set_yticks([])
    a.set_title("%d.  c = %.4g %+ .4gi" % (i + 1, c.real, c.imag),
                color=FG, fontsize=9.5, pad=5)
    a.set_xlabel(label, color=ACC, fontsize=8.5, labelpad=4)

fig.text(0.5, 0.028,
         "c inside the Mandelbrot set gives a connected Julia set; c outside gives "
         "totally disconnected dust. The set is a map of Julia-set behaviour.",
         color=ACC, fontsize=8.5, ha="center")
fig.savefig("docs/gallery.png", dpi=140, facecolor=BG)
print("saved docs/gallery.png")
