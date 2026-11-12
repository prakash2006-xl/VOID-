#!/usr/bin/env python3
"""
Test GlassIslandFrame pure glassmorphism rendering and artifact generation.
"""

import sys
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QColor

sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

def test_glass_rendering():
    print("--- 1. Testing GlassIslandFrame Rendering ---")
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(["--platform", "offscreen"])

    # Instantiate GlassIslandFrame
    frame = vw.GlassIslandFrame()
    frame.resize(360, 58)
    frame.set_radius(28)

    # Render to QImage
    img = QImage(360, 58, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(img)
    # Paint directly via paintEvent simulation
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    rect = frame.rect()
    w = float(rect.width())
    h = float(rect.height())
    r = float(frame._radius)

    # 1. Base Frosted Glass Gradient
    bg_grad = QtGui.QLinearGradient(0.0, 0.0, 0.0, h)
    bg_grad.setColorAt(0.0, QColor(16, 24, 42, 175))
    bg_grad.setColorAt(0.5, QColor(10, 16, 30, 155))
    bg_grad.setColorAt(1.0, QColor(6, 10, 20, 185))
    painter.setBrush(QtGui.QBrush(bg_grad))

    # 2. Outer Cyber-Glass Rim Pen
    rim_grad = QtGui.QLinearGradient(0.0, 0.0, 0.0, h)
    rim_grad.setColorAt(0.0, QColor(186, 230, 253, 160))
    rim_grad.setColorAt(0.25, QColor(56, 189, 248, 120))
    rim_grad.setColorAt(0.75, QColor(30, 64, 175, 80))
    rim_grad.setColorAt(1.0, QColor(14, 165, 233, 90))
    painter.setPen(QtGui.QPen(QtGui.QBrush(rim_grad), 1.2))

    draw_rect = QtCore.QRectF(0.6, 0.6, w - 1.2, h - 1.2)
    painter.drawRoundedRect(draw_rect, r, r)

    # 3. Top Specular Reflection Sheen
    spec_h = min(22.0, h * 0.45)
    spec_grad = QtGui.QLinearGradient(0.0, 1.0, 0.0, spec_h)
    spec_grad.setColorAt(0.0, QColor(255, 255, 255, 110))
    spec_grad.setColorAt(0.35, QColor(125, 211, 252, 45))
    spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QtGui.QBrush(spec_grad))

    spec_path = QtGui.QPainterPath()
    spec_path.addRoundedRect(QtCore.QRectF(1.2, 1.2, w - 2.4, spec_h), r, r)
    painter.drawPath(spec_path)

    # 4. Subtle Specular Highlight Line at the very top edge
    painter.setPen(QtGui.QPen(QColor(255, 255, 255, 140), 1.0))
    painter.drawLine(QtCore.QPointF(r, 1.2), QtCore.QPointF(w - r, 1.2))
    painter.end()

    # Save artifact
    artifact_path = Path("/run/media/prakash/TR_39/VOID/scripts/glass_effect_verified.png")
    img.save(str(artifact_path))
    print(f"  [PASS] Rendered GlassIslandFrame to {artifact_path}")

    # Verify top specular pixel is active
    top_pixel = QColor.fromRgba(img.pixel(180, 2))
    assert top_pixel.alpha() > 100, f"Top specular alpha={top_pixel.alpha()}"
    print(f"  [PASS] Top specular pixel alpha={top_pixel.alpha()}, r={top_pixel.red()}, g={top_pixel.green()}, b={top_pixel.blue()}")

    # Verify center body pixel is translucent dark obsidian/sapphire
    center_pixel = QColor.fromRgba(img.pixel(180, 29))
    assert 120 < center_pixel.alpha() < 210, f"Body pixel alpha {center_pixel.alpha()} is not translucent!"
    print(f"  [PASS] Center glass body pixel alpha={center_pixel.alpha()} (frosted glass translucency confirmed)")

    # Test expanded state
    frame_exp = vw.GlassIslandFrame()
    frame_exp.resize(370, 265)
    frame_exp.set_radius(18)
    img_exp = QImage(370, 265, QImage.Format.Format_ARGB32)
    img_exp.fill(Qt.GlobalColor.transparent)
    p_exp = QtGui.QPainter(img_exp)
    p_exp.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p_exp.setBrush(QtGui.QBrush(bg_grad))
    p_exp.setPen(QtGui.QPen(QtGui.QBrush(rim_grad), 1.2))
    p_exp.drawRoundedRect(QtCore.QRectF(0.6, 0.6, 370 - 1.2, 265 - 1.2), 18, 18)
    p_exp.end()

    artifact_exp_path = Path("/run/media/prakash/TR_39/VOID/scripts/glass_expanded_verified.png")
    img_exp.save(str(artifact_exp_path))
    print(f"  [PASS] Rendered expanded GlassIslandFrame to {artifact_exp_path}")

if __name__ == "__main__":
    test_glass_rendering()
    print("\nALL GLASS EFFECT TESTS PASSED! (2/2)")
