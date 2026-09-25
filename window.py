import ctypes
import re
import sys

WIN_KEY_COLOR = "#010203"  # Windows color key, must not appear in the sprites

SHAPE_BOUNDING, SHAPE_SET, UNSORTED = 0, 0, 0  # X11 SHAPE constants


class XRectangle(ctypes.Structure):
    _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]


def alpha_to_rects(image):
    """Convert the alpha channel into (x, y, w, h) row runs for an X11 mask."""
    width, height = image.size
    alpha = image.getchannel("A").tobytes()
    rects = []
    for y in range(height):
        row = alpha[y * width:(y + 1) * width]
        rects += [(m.start(), y, m.end() - m.start(), 1)
                  for m in re.finditer(rb"[^\x00]+", row)]
    return rects


class Transparency:
    """Makes a borderless Tk window see-through around the sprite."""

    def __init__(self, root):
        self.root = root
        self.bg = "#000000"       # background color for widgets in the window
        self.needs_mask = False   # True when a mask must be sent per frame
        self._targets = None

        if sys.platform.startswith("win"):
            self.bg = WIN_KEY_COLOR
            root.attributes("-transparentcolor", WIN_KEY_COLOR)
        elif sys.platform == "darwin":
            self.bg = "systemTransparent"
            root.attributes("-transparent", True)
        else:
            self._init_x11()

    def _init_x11(self):
        # Tk has no transparency on X11, so the window is clipped with the SHAPE
        # extension. libX11 is called directly: python-xlib cannot authenticate
        # on GNOME/Wayland (XWayland uses a wildcard Xauthority entry).
        try:
            self._x11 = ctypes.CDLL("libX11.so.6")
            self._xext = ctypes.CDLL("libXext.so.6")
            self._declare_functions()
            self._dpy = self._x11.XOpenDisplay(None)
            if not self._dpy:
                raise RuntimeError("cannot open the X display")
            events, errors = ctypes.c_int(), ctypes.c_int()
            if not self._xext.XShapeQueryExtension(
                    self._dpy, ctypes.byref(events), ctypes.byref(errors)):
                raise RuntimeError("the X server has no SHAPE extension")
        except (OSError, RuntimeError) as error:
            print(f"[window] no transparency: {error}", file=sys.stderr)
            return
        self.needs_mask = True

    def _declare_functions(self):
        c = ctypes
        self._x11.XOpenDisplay.argtypes = [c.c_char_p]
        self._x11.XOpenDisplay.restype = c.c_void_p
        self._x11.XQueryTree.argtypes = [
            c.c_void_p, c.c_ulong, c.POINTER(c.c_ulong), c.POINTER(c.c_ulong),
            c.POINTER(c.POINTER(c.c_ulong)), c.POINTER(c.c_uint)]
        self._x11.XQueryTree.restype = c.c_int
        self._x11.XFree.argtypes = [c.c_void_p]
        self._x11.XFlush.argtypes = [c.c_void_p]
        self._xext.XShapeQueryExtension.argtypes = [
            c.c_void_p, c.POINTER(c.c_int), c.POINTER(c.c_int)]
        self._xext.XShapeQueryExtension.restype = c.c_int
        self._xext.XShapeCombineRectangles.argtypes = [
            c.c_void_p, c.c_ulong, c.c_int, c.c_int, c.c_int,
            c.POINTER(XRectangle), c.c_int, c.c_int, c.c_int]
        self._xext.XShapeCombineRectangles.restype = None

    def apply(self, rects):
        """Clip the window to the given rectangles (X11 only)."""
        if not self.needs_mask:
            return
        if self._targets is None:
            self._find_targets()
        array = (XRectangle * len(rects))(*rects)
        for window in self._targets:
            self._xext.XShapeCombineRectangles(
                self._dpy, window, SHAPE_BOUNDING, 0, 0,
                array, len(rects), SHAPE_SET, UNSORTED)
        self._x11.XFlush(self._dpy)

    def _find_targets(self):
        # Tk wraps each toplevel in a parent window, both need the mask
        window = self.root.winfo_id()
        root_id, parent = ctypes.c_ulong(), ctypes.c_ulong()
        children = ctypes.POINTER(ctypes.c_ulong)()
        count = ctypes.c_uint()
        self._x11.XQueryTree(self._dpy, window, ctypes.byref(root_id),
                             ctypes.byref(parent), ctypes.byref(children),
                             ctypes.byref(count))
        if children:
            self._x11.XFree(ctypes.cast(children, ctypes.c_void_p))
        self._targets = [window]
        if parent.value != root_id.value:
            self._targets.append(parent.value)
