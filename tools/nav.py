"""Tap a sequence of buttons in PPSSPP and screenshot. usage: python nav.py out.png btn[:wait] ..."""
import sys
from ppsspp_dbg import Dbg
with Dbg() as d:
    if d.is_stepping():
        d.call('cpu.resume')
    for tok in sys.argv[2:]:
        b, _, w = tok.partition(':')
        d.tap(b, wait=float(w or 1.0))
Dbg.grab_window(sys.argv[1])
