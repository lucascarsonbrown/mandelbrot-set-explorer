"""Streamlit port of the Mandelbrot / Julia set explorer.

The desktop app (SMJExplorer.py) draws through Tkinter and cannot run on a
server, so this is a separate front end over the same mathematics: the
escape-time iteration z -> z^2 + c, read two ways.

Rendering is vectorised with NumPy and cached, because a Community Cloud
container is one modest CPU and every widget change reruns the script.

    streamlit run app.py
"""
from __future__ import annotations

import numpy as np
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

# ── page ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Mandelbrot & Julia Explorer",
                   page_icon="🌀", layout="wide")

MANDELBROT_HOME = (-2.2, 0.8, -1.25, 1.25)
JULIA_HOME = (-1.6, 1.6, -1.2, 1.2)
ESCAPE = 2.0

PALETTES = {
    "forest": ["#101a0e", "#2b3819", "#576d3b", "#a48854", "#f1f5fc", "#a48854"],
    "ember": ["#0b0a10", "#3b1338", "#8c2d43", "#e0703a", "#f6d67a", "#e0703a"],
    "ice": ["#05080f", "#12314f", "#2f6f96", "#7fc4d6", "#f2fbff", "#7fc4d6"],
    "monochrome": ["#000000", "#3a3a3a", "#787878", "#b4b4b4", "#ffffff", "#b4b4b4"],
}


# ── colour ────────────────────────────────────────────────────────────────────

def _ramp(hex_colors: list[str], n: int = 512) -> np.ndarray:
    """Linear RGB ramp through the given hex stops, as uint8."""
    stops = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in hex_colors],
                     dtype=float)
    x = np.linspace(0, len(stops) - 1, n)
    lo = np.clip(np.floor(x).astype(int), 0, len(stops) - 1)
    hi = np.clip(lo + 1, 0, len(stops) - 1)
    t = (x - lo)[:, None]
    return (stops[lo] * (1 - t) + stops[hi] * t).astype(np.uint8)


# ── the iteration ─────────────────────────────────────────────────────────────

def _grid(view: tuple[float, float, float, float], px: int):
    re_lo, re_hi, im_lo, im_hi = view
    height = max(1, int(px * (im_hi - im_lo) / (re_hi - re_lo)))
    re = np.linspace(re_lo, re_hi, px)
    im = np.linspace(im_hi, im_lo, height)          # top row = high imaginary
    return re[None, :] + 1j * im[:, None]


@st.cache_data(show_spinner=False, max_entries=48)
def escape_time(view, px, max_iter, julia_c=None):
    """Smooth escape time. julia_c=None renders the Mandelbrot set.

    julia_c is a plain (re, im) tuple rather than a complex — Streamlit's cache
    cannot hash complex, and passing one silently costs the whole cache.

    Returns a float array; points that never escape are NaN, so the interior
    can be painted as a solid colour instead of as another band.
    """
    Z0 = _grid(view, px)
    if julia_c is None:
        C, Z = Z0, np.zeros_like(Z0)                # vary c, fix z0 = 0
    else:
        c = complex(julia_c[0], julia_c[1])
        C, Z = np.full(Z0.shape, c), Z0.copy()      # fix c, vary z0

    out = np.full(Z.shape, np.nan)
    live = np.ones(Z.shape, dtype=bool)
    for n in range(max_iter):
        Z[live] = Z[live] ** 2 + C[live]
        gone = live & (np.abs(Z) > ESCAPE)
        if gone.any():
            # normalised iteration count removes the visible integer banding
            out[gone] = n + 1 - np.log(np.log(np.abs(Z[gone]))) / np.log(2)
        live &= ~gone
        if not live.any():
            break
    return out


@st.cache_data(show_spinner=False, max_entries=16)
def period_map(view, px, max_iter, max_period=32):
    """Cycle length of the orbit for points inside the set, else 0.

    Runs a transient, then looks for the smallest p with |z_{n+p} - z_n| < tol.
    """
    C = _grid(view, px)
    Z = np.zeros_like(C)
    for _ in range(max_iter):
        Z = Z ** 2 + C
        np.nan_to_num(Z, copy=False, nan=1e9, posinf=1e9, neginf=-1e9)

    inside = np.abs(Z) <= ESCAPE
    period = np.zeros(C.shape, dtype=np.int16)
    anchor = Z.copy()
    W = Z.copy()
    for p in range(1, max_period + 1):
        W = W ** 2 + C
        np.nan_to_num(W, copy=False, nan=1e9, posinf=1e9, neginf=-1e9)
        hit = inside & (period == 0) & (np.abs(W - anchor) < 1e-6)
        period[hit] = p
    return np.where(inside, period, 0)


def in_mandelbrot(c: complex, max_iter: int = 2000) -> bool:
    z = 0j
    for _ in range(max_iter):
        z = z * z + c
        if abs(z) > ESCAPE:
            return False
    return True


def orbit_period(c: complex, max_iter: int = 3000, max_period: int = 64):
    """Length of the cycle the orbit of 0 settles into, or None.

    This is the eventual cycle, which is the attracting cycle for c in the
    interior of a bulb but a repelling one at a pre-periodic (Misiurewicz)
    parameter such as c = i. Parabolic points on a bulb boundary converge too
    slowly to detect and come back None, which is why the caller treats the
    period as optional rather than as a fact about every c.
    """
    z = 0j
    for _ in range(max_iter):
        z = z * z + c
        if abs(z) > ESCAPE:
            return None
    anchor, w = z, z
    for p in range(1, max_period + 1):
        w = w * w + c
        if abs(w - anchor) < 1e-9:
            return p
    return None


# ── rendering ─────────────────────────────────────────────────────────────────

def colourise(counts: np.ndarray, palette: str, interior: str = "#0a0f08"):
    ramp = _ramp(PALETTES[palette])
    finite = np.isfinite(counts)
    img = np.zeros(counts.shape + (3,), dtype=np.uint8)
    img[...] = [int(interior[i:i + 2], 16) for i in (1, 3, 5)]
    if finite.any():
        v = np.sqrt(np.where(finite, counts, 0))
        hi = v[finite].max() or 1.0
        idx = np.clip((v / hi * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)
        img[finite] = ramp[idx[finite]]
    return img


def colourise_period(periods: np.ndarray, palette: str):
    ramp = _ramp(PALETTES[palette])
    img = np.zeros(periods.shape + (3,), dtype=np.uint8)
    inside = periods > 0
    if inside.any():
        # a stable hue per period, so bulbs read as flat regions
        idx = (periods[inside].astype(int) * 47) % len(ramp)
        img[inside] = ramp[idx]
    return img


def view_after_zoom(view, cx, cy, factor):
    re_lo, re_hi, im_lo, im_hi = view
    w, h = (re_hi - re_lo) * factor / 2, (im_hi - im_lo) * factor / 2
    return (cx - w, cx + w, cy - h, cy + h)


def pixel_to_complex(view, px, height, x, y):
    re_lo, re_hi, im_lo, im_hi = view
    return (re_lo + (re_hi - re_lo) * x / max(px - 1, 1),
            im_hi - (im_hi - im_lo) * y / max(height - 1, 1))


# ── state ─────────────────────────────────────────────────────────────────────

ss = st.session_state
ss.setdefault("m_view", MANDELBROT_HOME)
ss.setdefault("j_view", JULIA_HOME)
ss.setdefault("c", -0.12 + 0.75j)
ss.setdefault("last_click", None)

# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("controls")

    click_mode = st.radio(
        "clicking the Mandelbrot set",
        ["picks c for the Julia set", "zooms in"],
        help="The correspondence between the two panels is the whole point, so "
             "picking c is the default.",
    )
    st.divider()

    max_iter = st.slider("max iterations", 50, 1000, 300, 50,
                         help="Higher resolves finer boundary detail and costs time.")
    px = st.select_slider("resolution", [300, 400, 500, 650, 800], value=500)
    palette = st.selectbox("palette", list(PALETTES), index=0)
    show_period = st.checkbox(
        "colour the Mandelbrot set by period", value=False,
        help="Each bulb contains parameters whose orbit settles into a cycle of "
             "one fixed length. Colouring by that length makes the bulbs flat.")

    st.divider()
    st.caption("famous parameters")
    presets = {
        "Douady rabbit": -0.12 + 0.75j,
        "Basilica": -1.0 + 0j,
        "Dendrite": complex(0, 1),
        "San Marco": -0.75 + 0j,
        "Siegel disk": -0.390541 - 0.586788j,
        "Cantor dust (outside)": 0.40 + 0.35j,
    }
    cols = st.columns(2)
    for i, (name, value) in enumerate(presets.items()):
        if cols[i % 2].button(name, use_container_width=True):
            ss.c = value
            ss.j_view = JULIA_HOME
            st.rerun()

    st.divider()
    re_in = st.number_input("Re(c)", value=float(ss.c.real), format="%.6f", step=0.01)
    im_in = st.number_input("Im(c)", value=float(ss.c.imag), format="%.6f", step=0.01)
    if st.button("set c", use_container_width=True):
        ss.c = complex(re_in, im_in)
        ss.j_view = JULIA_HOME
        st.rerun()

# ── header ────────────────────────────────────────────────────────────────────

st.title("Mandelbrot & Julia set explorer")
st.caption(
    "Both sets come from one iteration, **z → z² + c**. The Mandelbrot set "
    "fixes z₀ = 0 and asks which **c** stay bounded. A Julia set fixes **c** "
    "and asks which **z₀** stay bounded. Click the left panel to choose c and "
    "watch the right panel answer."
)

left, right = st.columns(2, gap="medium")

# ── Mandelbrot ────────────────────────────────────────────────────────────────

with left:
    view = ss.m_view
    if show_period:
        data = period_map(view, px, min(max_iter, 400))
        img = colourise_period(data, palette)
    else:
        data = escape_time(view, px, max_iter, None)
        img = colourise(data, palette)
    height = img.shape[0]

    st.subheader("Mandelbrot set")
    click = streamlit_image_coordinates(Image.fromarray(img), key="mandel",
                                        width=px)
    if click and click != ss.last_click:
        ss.last_click = click
        cx, cy = pixel_to_complex(view, px, height, click["x"], click["y"])
        if click_mode == "zooms in":
            ss.m_view = view_after_zoom(view, cx, cy, 0.4)
        else:
            ss.c = complex(cx, cy)
            ss.j_view = JULIA_HOME
        st.rerun()

    zoom_out, reset, _ = st.columns([1, 1, 2])
    if zoom_out.button("zoom out", use_container_width=True):
        mid_r = (view[0] + view[1]) / 2
        mid_i = (view[2] + view[3]) / 2
        ss.m_view = view_after_zoom(view, mid_r, mid_i, 2.5)
        st.rerun()
    if reset.button("reset", use_container_width=True):
        ss.m_view = MANDELBROT_HOME
        st.rerun()

    span = ss.m_view[1] - ss.m_view[0]
    st.caption(f"view width {span:.3g}  ·  zoom ×{(MANDELBROT_HOME[1] - MANDELBROT_HOME[0]) / span:,.0f}")

# ── Julia ─────────────────────────────────────────────────────────────────────

with right:
    c = ss.c
    jdata = escape_time(ss.j_view, px, max_iter, (c.real, c.imag))
    jimg = colourise(jdata, palette)

    st.subheader("Julia set")
    jclick = streamlit_image_coordinates(Image.fromarray(jimg), key="julia",
                                         width=px)
    if jclick and jclick != ss.last_click:
        ss.last_click = jclick
        zx, zy = pixel_to_complex(ss.j_view, px, jimg.shape[0],
                                  jclick["x"], jclick["y"])
        ss.j_view = view_after_zoom(ss.j_view, zx, zy, 0.4)
        st.rerun()

    jzoom_out, jreset, _ = st.columns([1, 1, 2])
    if jzoom_out.button("zoom out", use_container_width=True, key="jzo"):
        mid_r = (ss.j_view[0] + ss.j_view[1]) / 2
        mid_i = (ss.j_view[2] + ss.j_view[3]) / 2
        ss.j_view = view_after_zoom(ss.j_view, mid_r, mid_i, 2.5)
        st.rerun()
    if jreset.button("reset", use_container_width=True, key="jr"):
        ss.j_view = JULIA_HOME
        st.rerun()

    inside = in_mandelbrot(c)
    period = orbit_period(c) if inside else None
    st.caption(f"c = {c.real:.6f} {'+' if c.imag >= 0 else '−'} {abs(c.imag):.6f}i")
    if inside:
        st.success(
            f"**c is inside the Mandelbrot set**, so this Julia set is "
            f"**connected** — one piece."
            + (f" The orbit settles into a cycle of period **{period}**."
               if period else "")
        )
    else:
        st.warning(
            "**c is outside the Mandelbrot set**, so this Julia set is "
            "**totally disconnected** — Cantor dust, with no piece joined to "
            "any other."
        )

st.divider()
st.markdown(
    "That last box is the whole reason the two panels sit side by side. "
    "Whether a Julia set holds together is decided entirely by whether its "
    "parameter lies inside the Mandelbrot set — which makes the left panel a "
    "map of every Julia set at once. "
    "[Source and the desktop version]"
    "(https://github.com/lucascarsonbrown/mandelbrot-set-explorer)."
)
