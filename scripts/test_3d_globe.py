#!/usr/bin/env python3
"""
Test script to render and verify the 3D Neural Plexus Globe with Glitter Effects.
"""

import math
import random
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QPoint, QPointF, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient, QLinearGradient, QPolygonF, QPixmap

class Node3D:
    def __init__(self, x: float, y: float, z: float, is_core: bool = False):
        self.x = x
        self.y = y
        self.z = z
        self.is_core = is_core
        self.pulse = random.random()
        self.pulse_speed = 0.05 + random.random() * 0.08

class GlitterParticle:
    def __init__(self, x: float, y: float, z: float, speed: float, phase: float, max_size: float = 2.0):
        self.x = x
        self.y = y
        self.z = z
        self.speed = speed
        self.phase = phase
        self.max_size = max_size

class NeuralGlobe3D(QtWidgets.QWidget):
    def __init__(self, size: int = 38, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._mode = "thinking"  # idle, listening, thinking, executing, speaking, empathy, celebrate
        self._audio_level = 0.0
        self._phase = 0.0
        self._yaw = 0.0
        self._pitch = 0.2
        self._roll = 0.0

        # Build 3D sphere lattice
        self._nodes: list[Node3D] = []
        self._build_sphere_mesh()

        # Build glitter particles
        self._glitters: list[GlitterParticle] = []
        self._build_glitters()

        # Dynamic Synaptic Pulse Packets
        self._pulses = [] # list of (from_idx, to_idx, progress, speed, color)

    def _build_sphere_mesh(self):
        self._nodes.clear()
        num_surface = 22
        # Fibonacci spiral on sphere
        phi = math.pi * (3.0 - math.sqrt(5.0))  # golden angle
        for i in range(num_surface):
            y = 1.0 - (i / float(num_surface - 1)) * 2.0  # from 1 to -1
            radius = math.sqrt(max(0.0, 1.0 - y * y))
            theta = phi * i
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            self._nodes.append(Node3D(x, y, z, is_core=False))

        # Core internal nodes (depth constellation)
        core_positions = [
            (0.0, 0.0, 0.0),
            (0.35, 0.2, -0.2),
            (-0.3, -0.25, 0.15),
            (0.15, -0.35, -0.25),
            (-0.2, 0.3, 0.25),
            (0.25, 0.1, 0.35),
        ]
        for cx, cy, cz in core_positions:
            self._nodes.append(Node3D(cx, cy, cz, is_core=True))

        # Precalculate edge pairs within distance threshold
        self._edges: list[tuple[int, int, float]] = []
        threshold = 0.95
        for i in range(len(self._nodes)):
            for j in range(i + 1, len(self._nodes)):
                n1 = self._nodes[i]
                n2 = self._nodes[j]
                d = math.sqrt((n1.x - n2.x)**2 + (n1.y - n2.y)**2 + (n1.z - n2.z)**2)
                if d < threshold:
                    self._edges.append((i, j, d))

    def _build_glitters(self):
        self._glitters.clear()
        for _ in range(18):
            # Distributed within radius 1.15
            u = random.random()
            r = 0.3 + 0.85 * (u ** (1.0 / 3.0))
            costheta = random.uniform(-1, 1)
            phi = random.uniform(0, 2 * math.pi)
            sintheta = math.sqrt(max(0.0, 1.0 - costheta * costheta))
            x = r * sintheta * math.cos(phi)
            y = r * sintheta * math.sin(phi)
            z = r * costheta
            speed = random.uniform(2.5, 6.0)
            phase = random.uniform(0, 2 * math.pi)
            size = random.uniform(1.2, 2.4)
            self._glitters.append(GlitterParticle(x, y, z, speed, phase, size))

    def set_mode(self, mode: str):
        self._mode = mode
        self.update()

    def set_audio_level(self, lvl: float):
        self._audio_level = max(0.0, min(1.0, lvl))
        self.update()

    def update_simulation(self):
        self._phase += 0.06

        # Rotation speeds according to state
        if self._mode == "thinking":
            yaw_speed = 0.055
            pitch_speed = 0.025
        elif self._mode == "executing":
            yaw_speed = 0.075
            pitch_speed = 0.015
        elif self._mode == "listening":
            yaw_speed = 0.035 + self._audio_level * 0.05
            pitch_speed = 0.018
        elif self._mode == "celebrate":
            yaw_speed = 0.08
            pitch_speed = 0.04
        else:  # idle
            yaw_speed = 0.02
            pitch_speed = 0.008

        self._yaw += yaw_speed
        self._pitch += pitch_speed
        self._roll = math.sin(self._phase * 0.5) * 0.15

        # Update node pulses
        for n in self._nodes:
            n.pulse = (n.pulse + n.pulse_speed) % 1.0

        # Spawn synaptic packets during thinking/executing
        if self._mode in ["thinking", "executing"] and self._edges:
            if random.random() < (0.35 if self._mode == "thinking" else 0.5):
                edge = random.choice(self._edges)
                # choose direction
                if random.random() < 0.5:
                    from_idx, to_idx = edge[0], edge[1]
                else:
                    from_idx, to_idx = edge[1], edge[0]
                speed = random.uniform(0.08, 0.18)
                self._pulses.append([from_idx, to_idx, 0.0, speed])

        # Advance pulses
        active_pulses = []
        for p in self._pulses:
            p[2] += p[3]
            if p[2] < 1.0:
                active_pulses.append(p)
        self._pulses = active_pulses

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        globe_radius = (min(w, h) / 2.0) - 2.5

        # 3D Rotation matrices
        cyaw, syaw = math.cos(self._yaw), math.sin(self._yaw)
        cpitch, spitch = math.cos(self._pitch), math.sin(self._pitch)
        croll, sroll = math.cos(self._roll), math.sin(self._roll)

        # 1. Base Ambient Spherical Glow / Glass Vignette
        # Color palettes according to mode
        if self._mode == "thinking":
            c_glow_center = QColor(254, 240, 138, 70)  # Bright golden amber / white
            c_glow_mid = QColor(245, 158, 11, 45)      # Deep electric amber
            c_rim = QColor(251, 191, 36, 160)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (245, 158, 11)
            c_pulse = QColor(255, 255, 220)
        elif self._mode == "executing":
            c_glow_center = QColor(56, 189, 248, 90)   # High-voltage cyan / laser blue
            c_glow_mid = QColor(14, 165, 233, 55)
            c_rim = QColor(56, 189, 248, 190)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (56, 189, 248)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "listening":
            pulse_extra = self._audio_level * 50
            c_glow_center = QColor(56, 189, 248, int(80 + pulse_extra))
            c_glow_mid = QColor(6, 182, 212, int(50 + pulse_extra))
            c_rim = QColor(34, 211, 238, 200)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (34, 211, 238)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "speaking":
            c_glow_center = QColor(232, 121, 249, 85)  # Neural violet / magenta
            c_glow_mid = QColor(192, 132, 252, 50)
            c_rim = QColor(216, 180, 254, 180)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (192, 132, 252)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "empathy":
            c_glow_center = QColor(251, 113, 133, 85)  # Warm Rose / Coral
            c_glow_mid = QColor(244, 63, 94, 50)
            c_rim = QColor(253, 164, 175, 180)
            c_core_node = QColor(255, 241, 242)
            c_synapse_base = (244, 63, 94)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "celebrate":
            c_glow_center = QColor(52, 211, 153, 90)   # Emerald / Golden
            c_glow_mid = QColor(16, 185, 129, 55)
            c_rim = QColor(110, 231, 183, 190)
            c_core_node = QColor(254, 240, 138)
            c_synapse_base = (52, 211, 153)
            c_pulse = QColor(255, 255, 255)
        else: # Idle
            c_glow_center = QColor(56, 189, 248, 50)   # Cosmic deep sapphire / cyan
            c_glow_mid = QColor(30, 58, 138, 30)
            c_rim = QColor(56, 189, 248, 110)
            c_core_node = QColor(240, 249, 255)
            c_synapse_base = (56, 189, 248)
            c_pulse = QColor(255, 255, 255)

        # Ambient backing sphere gradient
        bg_radial = QRadialGradient(cx, cy, globe_radius * 1.05)
        bg_radial.setColorAt(0.0, c_glow_center)
        bg_radial.setColorAt(0.65, c_glow_mid)
        bg_radial.setColorAt(1.0, QColor(10, 14, 26, 0))
        painter.setBrush(QBrush(bg_radial))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), globe_radius, globe_radius)

        # 2. Transform 3D Nodes to 2D Screen Space with Depth Perspective
        projected_nodes = []
        cam_dist = 2.4
        radial_scale = globe_radius * 0.88

        # In listening mode, slightly expand nodes based on audio
        if self._mode == "listening":
            radial_scale *= (1.0 + self._audio_level * 0.18)

        for n in self._nodes:
            # Yaw rotation (around Y)
            x1 = n.x * cyaw + n.z * syaw
            z1 = -n.x * syaw + n.z * cyaw
            y1 = n.y

            # Pitch rotation (around X)
            y2 = y1 * cpitch - z1 * spitch
            z2 = y1 * spitch + z1 * cpitch
            x2 = x1

            # Roll rotation (around Z)
            x3 = x2 * croll - y2 * sroll
            y3 = x2 * sroll + y2 * croll
            z3 = z2

            # Perspective projection
            persp = cam_dist / (cam_dist + z3)
            sx = cx + x3 * radial_scale * persp
            sy = cy + y3 * radial_scale * persp

            # Normalized depth: z_norm in [0 (furthest back), 1 (closest)]
            z_norm = (z3 + 1.0) / 2.0
            projected_nodes.append((sx, sy, z3, z_norm, n))

        # 3. Draw Synaptic Plexus Filaments (interconnecting lines)
        # Sort edges by average depth so furthest lines render underneath
        edge_depth_list = []
        for idx1, idx2, d in self._edges:
            p1 = projected_nodes[idx1]
            p2 = projected_nodes[idx2]
            avg_z = (p1[2] + p2[2]) / 2.0
            edge_depth_list.append((avg_z, idx1, idx2, d))
        edge_depth_list.sort(key=lambda item: item[0])

        r_base, g_base, b_base = c_synapse_base
        for avg_z, idx1, idx2, dist in edge_depth_list:
            p1 = projected_nodes[idx1]
            p2 = projected_nodes[idx2]
            avg_norm = (avg_z + 1.0) / 2.0  # 0 to 1

            # Distance factor: closer nodes have stronger connection
            dist_factor = max(0.0, 1.0 - (dist / 0.95))

            # Opacity based on 3D depth and proximity
            alpha = int(15 + 175 * avg_norm * dist_factor)
            if self._mode in ["thinking", "executing"]:
                alpha = min(255, int(alpha * 1.35))

            # Line width: closer lines are thicker
            pen_w = 0.6 + 1.1 * avg_norm
            pen = QPen(QColor(r_base, g_base, b_base, alpha), pen_w)
            painter.setPen(pen)
            painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))

        # 4. Draw Active Neural Synaptic Packets (Traveling Sparks)
        for from_i, to_i, prog, _ in self._pulses:
            p_from = projected_nodes[from_i]
            p_to = projected_nodes[to_i]
            # Interpolated position
            px = p_from[0] + (p_to[0] - p_from[0]) * prog
            py = p_from[1] + (p_to[1] - p_from[1]) * prog
            pz = p_from[2] + (p_to[2] - p_from[2]) * prog
            pz_norm = (pz + 1.0) / 2.0

            pulse_size = 1.5 + 1.8 * pz_norm
            # Glowing spark
            spark_grad = QRadialGradient(px, py, pulse_size * 2.0)
            spark_grad.setColorAt(0.0, c_pulse)
            spark_grad.setColorAt(0.4, QColor(r_base, g_base, b_base, 220))
            spark_grad.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
            painter.setBrush(QBrush(spark_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(px, py), pulse_size * 1.8, pulse_size * 1.8)

        # 5. Draw 3D Neural Nodes (Spherical Points with Depth Bokeh)
        # Sort nodes back-to-front
        sorted_nodes = sorted(projected_nodes, key=lambda item: item[2])
        for sx, sy, z, z_norm, n in sorted_nodes:
            # Base node radius modulated by depth
            node_r = 1.2 + 2.2 * z_norm
            if n.is_core:
                node_r *= 1.2

            # Pulse glow
            pulse_mult = 1.0 + 0.2 * math.sin(n.pulse * 2 * math.pi)
            cur_r = node_r * pulse_mult

            # Halo for foreground nodes
            if z_norm > 0.45:
                halo_r = cur_r * (2.2 if self._mode == "thinking" else 1.8)
                halo = QRadialGradient(sx, sy, halo_r)
                halo_alpha = int(140 * z_norm)
                halo.setColorAt(0.0, QColor(r_base, g_base, b_base, halo_alpha))
                halo.setColorAt(0.6, QColor(r_base, g_base, b_base, int(halo_alpha * 0.4)))
                halo.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
                painter.setBrush(QBrush(halo))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(sx, sy), halo_r, halo_r)

            # Node Core (bright white-hot center for front nodes)
            core_grad = QRadialGradient(sx - 0.5, sy - 0.5, cur_r)
            core_alpha = int(80 + 175 * z_norm)
            core_grad.setColorAt(0.0, QColor(255, 255, 255, core_alpha))
            core_grad.setColorAt(0.5, QColor(r_base, g_base, b_base, core_alpha))
            core_grad.setColorAt(1.0, QColor(max(0, r_base - 50), max(0, g_base - 50), max(0, b_base - 50), core_alpha))
            painter.setBrush(QBrush(core_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(sx, sy), cur_r, cur_r)

        # 6. Draw 3D Glittering Particle Stars & Diamond Sparkles
        for g in self._glitters:
            # Rotate particle
            x1 = g.x * cyaw + g.z * syaw
            z1 = -g.x * syaw + g.z * cyaw
            y1 = g.y

            y2 = y1 * cpitch - z1 * spitch
            z2 = y1 * spitch + z1 * cpitch
            x2 = x1

            persp = cam_dist / (cam_dist + z2)
            gx = cx + x2 * radial_scale * 1.08 * persp
            gy = cy + y2 * radial_scale * 1.08 * persp
            gz_norm = (z2 + 1.0) / 2.0

            # Twinkle phase
            twinkle = 0.5 + 0.5 * math.sin(self._phase * g.speed + g.phase)
            spark_alpha = int(twinkle * (70 + 185 * gz_norm))

            if spark_alpha > 20:
                p_size = (0.8 + g.max_size * gz_norm) * (0.6 + 0.6 * twinkle)

                # If peak brightness and towards the front: draw 4-pointed diamond star flare!
                if twinkle > 0.82 and gz_norm > 0.5:
                    flare_len = p_size * 2.8
                    pen_flare = QPen(QColor(255, 255, 255, int(spark_alpha * 0.9)), 0.8)
                    painter.setPen(pen_flare)
                    painter.drawLine(QPointF(gx - flare_len, gy), QPointF(gx + flare_len, gy))
                    painter.drawLine(QPointF(gx, gy - flare_len), QPointF(gx, gy + flare_len))

                # Sparkle center dot
                spk = QRadialGradient(gx, gy, p_size)
                spk.setColorAt(0.0, QColor(255, 255, 255, spark_alpha))
                spk.setColorAt(0.5, QColor(r_base, g_base, b_base, int(spark_alpha * 0.8)))
                spk.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
                painter.setBrush(QBrush(spk))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(gx, gy), p_size, p_size)

        # 7. Holographic Glass Rim & Fresnel Shimmer
        rim_pen = QPen(c_rim, 1.2)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), globe_radius, globe_radius)

        # Inner specular reflection arc
        spec_grad = QLinearGradient(cx - globe_radius, cy - globe_radius, cx + globe_radius, cy + globe_radius)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 110))
        spec_grad.setColorAt(0.3, QColor(255, 255, 255, 30))
        spec_grad.setColorAt(0.7, QColor(255, 255, 255, 0))
        spec_pen = QPen(QBrush(spec_grad), 1.0)
        painter.setPen(spec_pen)
        painter.drawArc(
            int(cx - globe_radius + 1.5), int(cy - globe_radius + 1.5),
            int(globe_radius * 2 - 3), int(globe_radius * 2 - 3),
            45 * 16, 90 * 16
        )

# Render frames for testing
app = QtWidgets.QApplication([])
widget = NeuralGlobe3D(size=64) # Render at 64 for detailed inspection

for mode in ["thinking", "executing", "idle"]:
    widget.set_mode(mode)
    for _ in range(25):
        widget.update_simulation()
    
    pix = QPixmap(widget.size())
    pix.fill(QColor(13, 18, 30, 255))
    widget.render(pix)
    out_path = f"/run/media/prakash/TR_39/VOID/scripts/globe_{mode}.png"
    pix.save(out_path)
    print(f"Saved {mode} frame to {out_path}")

print("Test complete.")

