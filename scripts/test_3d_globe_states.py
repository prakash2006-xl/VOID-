#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for 3D Neural Plexus Globe & Holographic Acoustic Core.
Verifies all 3D modes: idle, listening, thinking, executing, speaking, empathy, celebrate.
"""

import os
import sys
from pathlib import Path
from PySide6 import QtWidgets, QtGui
from PySide6.QtGui import QPixmap, QColor

VOID_BIN = Path("/run/media/prakash/TR_39/VOID/bin")
sys.path.insert(0, str(VOID_BIN))

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", str(VOID_BIN / "void-widget.py"))
vw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vw)

os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

print("=================================================")
print("   3D NEURAL PLEXUS GLOBE VERIFICATION SUITE    ")
print("=================================================")

orb = vw.OrbWidget(size=36)

modes = ["idle", "listening", "thinking", "executing", "speaking", "empathy", "celebrate"]
passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {name} - {details}")
    else:
        failed += 1
        print(f"[FAIL] {name} - {details}")

# Test 1: Lattice geometry & connections
test(
    "3D Fibonacci Sphere Lattice Geometry",
    len(orb._nodes) == 28 and len(orb._edges) > 30,
    f"Total 3D nodes: {len(orb._nodes)} (22 surface + 6 core), edges: {len(orb._edges)}"
)

# Test 2: 3D Glitter Particle Constellation
test(
    "3D Glitter Particle Constellation",
    len(orb._glitters) == 18,
    f"Floating glitter particles: {len(orb._glitters)}"
)

# Test 3: Rendering & Simulation Across All Modes
for mode in modes:
    try:
        orb.set_mode(mode)
        if mode == "listening":
            orb.set_audio_level(0.75)
        
        # Advance simulation several frames
        for _ in range(15):
            orb._on_tick()

        pix = QPixmap(orb.size())
        pix.fill(QColor(0, 0, 0, 0))
        orb.render(pix)
        
        # Check non-empty rendering
        img = pix.toImage()
        has_pixels = any(img.pixelColor(x, y).alpha() > 0 for x in range(img.width()) for y in range(img.height()))
        test(f"3D Globe Rendering [{mode.upper()}]", has_pixels, f"Rendered 36x36 px with dynamic pulses: {len(orb._pulses)}")
    except Exception as e:
        test(f"3D Globe Rendering [{mode.upper()}]", False, f"Exception: {e}")

# Test 4: Dynamic Synaptic Pulse Spawning in Thinking & Executing
orb.set_mode("thinking")
for _ in range(30):
    orb._on_tick()
test(
    "Synaptic Pulse Traveling Packets",
    len(orb._pulses) > 0,
    f"Active traveling energy sparks in thinking: {len(orb._pulses)}"
)

orb.close()

print("=================================================")
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=================================================")

if failed > 0:
    os._exit(1)
os._exit(0)

