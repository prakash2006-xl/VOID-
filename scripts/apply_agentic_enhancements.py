#!/usr/bin/env python3
"""
VOID Agentic OS - Wiring Updater Script
Safely integrates the Multi-Agent framework into /run/media/prakash/TR_39/VOID/bin/void-widget.py:
1. Adds Agentic imports.
2. Extends OrbWidget with planning, verifying, recovering, and waiting_approval visual states.
3. Adds agentic_update signal and Supervisor initialization in AudioVoiceEngine.
4. Mounts AgentActivityCard into VoidMiniWidget and connects live timeline updates.
5. Adds Multi-Agent quick chip to the glass UI drawer.
Validates Python syntax before finalizing changes.
"""

import sys
import shutil
import py_compile
from pathlib import Path

TARGET_FILE = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")
BACKUP_FILE = Path(f"{TARGET_FILE}.bak_pre_agentic_patch")

def apply_patch():
    print(f"Reading target file: {TARGET_FILE}")
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Backup
    shutil.copy2(TARGET_FILE, BACKUP_FILE)
    print(f"Created safety backup at {BACKUP_FILE}")

    # 1. Imports
    old_import_anchor = "from PySide6.QtWidgets import (\n    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,\n    QPushButton, QLineEdit, QFrame, QScrollArea\n)"
    new_import = (
        old_import_anchor + "\n\n"
        "# Agentic Multi-Agent Framework Integration\n"
        "try:\n"
        "    from agentic import (\n"
        "        SupervisorAgent, ToolRegistry, AIProviderManager, PermissionManager,\n"
        "        AgentMemoryManager, AuditLogger, CompetitionDemos, AgentActivityCard,\n"
        "        WorkflowLifecycleState, TaskStatus\n"
        "    )\n"
        "except ImportError as e:\n"
        "    print(f'[VOID Agentic Import Notice] {e}', flush=True)\n"
    )

    if old_import_anchor not in content:
        raise ValueError("Could not find old_import_anchor in void-widget.py")
    content = content.replace(old_import_anchor, new_import, 1)

    # 2. OrbWidget speed additions
    old_orb_speed_anchor = (
        '        elif self._mode == "celebrate":\n'
        '            yaw_speed = 0.08\n'
        '            pitch_speed = 0.04\n'
        '        else:  # idle'
    )
    new_orb_speed = (
        '        elif self._mode == "celebrate":\n'
        '            yaw_speed = 0.08\n'
        '            pitch_speed = 0.04\n'
        '        elif self._mode == "planning":\n'
        '            yaw_speed = 0.045\n'
        '            pitch_speed = 0.020\n'
        '        elif self._mode == "verifying":\n'
        '            yaw_speed = 0.030\n'
        '            pitch_speed = 0.015\n'
        '        elif self._mode == "recovering":\n'
        '            yaw_speed = 0.085\n'
        '            pitch_speed = 0.035\n'
        '        elif self._mode == "waiting_approval":\n'
        '            yaw_speed = 0.015\n'
        '            pitch_speed = 0.005\n'
        '        else:  # idle'
    )
    if old_orb_speed_anchor not in content:
        raise ValueError("Could not find old_orb_speed_anchor in void-widget.py")
    content = content.replace(old_orb_speed_anchor, new_orb_speed, 1)

    # 3. OrbWidget color additions
    old_orb_color_anchor = (
        '        elif self._mode == "celebrate":\n'
        '            c_glow_center = QColor(52, 211, 153, 90)   # Emerald / Golden\n'
        '            c_glow_mid = QColor(16, 185, 129, 55)\n'
        '            c_rim = QColor(110, 231, 183, 190)\n'
        '            c_core_node = QColor(254, 240, 138)\n'
        '            c_synapse_base = (52, 211, 153)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        else: # Idle'
    )
    new_orb_color = (
        '        elif self._mode == "celebrate":\n'
        '            c_glow_center = QColor(52, 211, 153, 90)   # Emerald / Golden\n'
        '            c_glow_mid = QColor(16, 185, 129, 55)\n'
        '            c_rim = QColor(110, 231, 183, 190)\n'
        '            c_core_node = QColor(254, 240, 138)\n'
        '            c_synapse_base = (52, 211, 153)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        elif self._mode == "planning":\n'
        '            c_glow_center = QColor(168, 85, 247, 85)   # Royal Indigo / Violet\n'
        '            c_glow_mid = QColor(147, 51, 234, 50)\n'
        '            c_rim = QColor(192, 132, 252, 190)\n'
        '            c_core_node = QColor(250, 245, 255)\n'
        '            c_synapse_base = (168, 85, 247)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        elif self._mode == "verifying":\n'
        '            c_glow_center = QColor(250, 204, 21, 90)   # Crystalline Gold / Verifier\n'
        '            c_glow_mid = QColor(234, 179, 8, 55)\n'
        '            c_rim = QColor(253, 224, 71, 200)\n'
        '            c_core_node = QColor(255, 255, 255)\n'
        '            c_synapse_base = (234, 179, 8)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        elif self._mode == "recovering":\n'
        '            c_glow_center = QColor(251, 146, 60, 95)   # Corrective Deep Orange\n'
        '            c_glow_mid = QColor(234, 88, 12, 60)\n'
        '            c_rim = QColor(253, 186, 116, 200)\n'
        '            c_core_node = QColor(255, 255, 255)\n'
        '            c_synapse_base = (234, 88, 12)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        elif self._mode == "waiting_approval":\n'
        '            c_glow_center = QColor(244, 63, 94, 95)    # Pulsing Ruby Amber\n'
        '            c_glow_mid = QColor(225, 29, 72, 60)\n'
        '            c_rim = QColor(251, 113, 133, 210)\n'
        '            c_core_node = QColor(255, 228, 230)\n'
        '            c_synapse_base = (225, 29, 72)\n'
        '            c_pulse = QColor(255, 255, 255)\n'
        '        else: # Idle'
    )
    if old_orb_color_anchor not in content:
        raise ValueError("Could not find old_orb_color_anchor in void-widget.py")
    content = content.replace(old_orb_color_anchor, new_orb_color, 1)

    # 4. AudioVoiceEngine signal addition
    old_signal_anchor = (
        '    shutdown_requested = Signal(str, int)\n'
        '    terminate_requested = Signal()'
    )
    new_signal = (
        old_signal_anchor + '\n'
        '    agentic_update = Signal(object, object, object)  # (state, plan, current_task)'
    )
    if old_signal_anchor not in content:
        raise ValueError("Could not find old_signal_anchor in void-widget.py")
    content = content.replace(old_signal_anchor, new_signal, 1)

    # 5. AudioVoiceEngine.__init__ supervisor initialization
    old_init_anchor = "        self._active_tts_proc: subprocess.Popen | None = None"
    new_init = (
        old_init_anchor + "\n"
        "        # Multi-Agent Autonomous Supervisor & Competition Demos\n"
        "        try:\n"
        "            self._agent_tools = ToolRegistry()\n"
        "            self._agent_providers = AIProviderManager()\n"
        "            self._agent_perms = PermissionManager()\n"
        "            self._agent_memory = AgentMemoryManager()\n"
        "            self._agent_audit = AuditLogger()\n"
        "            self._supervisor = SupervisorAgent(\n"
        "                tools=self._agent_tools,\n"
        "                provider_manager=self._agent_providers,\n"
        "                permission_manager=self._agent_perms,\n"
        "                memory_manager=self._agent_memory,\n"
        "                audit_logger=self._agent_audit,\n"
        "                on_state_change=self._on_agentic_state_change,\n"
        "            )\n"
        "            self._demos = CompetitionDemos(self._supervisor)\n"
        "            print('[VOID Agentic] Multi-Agent Supervisor initialized successfully.', flush=True)\n"
        "        except Exception as _e:\n"
        "            print(f'[VOID Agentic Warning] Multi-Agent initialization skipped: {_e}', flush=True)\n"
        "            self._supervisor = None\n"
        "            self._demos = None\n"
    )
    if old_init_anchor not in content:
        raise ValueError("Could not find old_init_anchor in void-widget.py")
    content = content.replace(old_init_anchor, new_init, 1)

    # 6. AudioVoiceEngine callback and helper methods
    old_process_task_anchor = "    def _process_task(self, query: str) -> None:"
    agentic_engine_methods = (
        "    def _on_agentic_state_change(self, state, plan=None, current_task=None) -> None:\n"
        "        state_val = getattr(state, 'value', str(state)).lower()\n"
        "        if state_val in ['planning', 'verifying', 'recovering', 'waiting_approval']:\n"
        "            self.state_changed.emit(state_val)\n"
        "        elif state_val == 'executing':\n"
        "            self.state_changed.emit('executing')\n"
        "        elif state_val == 'completed':\n"
        "            self.state_changed.emit('celebrate')\n"
        "        self.agentic_update.emit(state, plan, current_task)\n\n"
        "    def _handle_agentic_response(self, query: str, summary_text: str, result_dict: dict[str, Any]) -> None:\n"
        "        state_name = result_dict.get('state', 'COMPLETED')\n"
        "        badge = f'Agentic: {state_name}'\n"
        "        artifacts = result_dict.get('artifacts', [])\n"
        "        thumb = artifacts[0] if artifacts else ''\n"
        "        if thumb:\n"
        "            self.last_generated_file = thumb\n"
        "        self._chat_history.append({'role': 'user', 'content': query})\n"
        "        self._chat_history.append({'role': 'assistant', 'content': summary_text})\n"
        "        if len(self._chat_history) > 16:\n"
        "            self._chat_history = self._chat_history[-16:]\n"
        "        print(f'[VOID Agentic] Task finished. Reply: {summary_text[:80]}... (Badge: {badge})', flush=True)\n"
        "        self.response_ready.emit(query, summary_text, badge, thumb)\n"
        "        self._speak_text(summary_text)\n\n"
        + old_process_task_anchor
    )
    if old_process_task_anchor not in content:
        raise ValueError("Could not find old_process_task_anchor in void-widget.py")
    content = content.replace(old_process_task_anchor, agentic_engine_methods, 1)

    # 7. Agentic interception in _process_task
    old_split_anchor = (
        "            # Sequential multi-command splitting\n"
        "            sub_commands = split_compound_commands(q_clean)"
    )
    new_interception = (
        "            # Check for Agentic Multi-Agent Workflows & Competition Demos\n"
        "            q_lower_check = q_clean.lower().strip()\n"
        "            if hasattr(self, '_supervisor') and self._supervisor:\n"
        "                if 'demo 1' in q_lower_check or 'agentic demo 1' in q_lower_check:\n"
        "                    self.state_changed.emit('planning')\n"
        "                    d_res = self._demos.run_demo_1_linux_diagnostics()\n"
        "                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 1 completed.'), d_res)\n"
        "                    return\n"
        "                elif 'demo 2' in q_lower_check or 'agentic demo 2' in q_lower_check:\n"
        "                    self.state_changed.emit('planning')\n"
        "                    d_res = self._demos.run_demo_2_test_driven_development()\n"
        "                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 2 completed.'), d_res)\n"
        "                    return\n"
        "                elif 'demo 3' in q_lower_check or 'agentic demo 3' in q_lower_check:\n"
        "                    self.state_changed.emit('planning')\n"
        "                    d_res = self._demos.run_demo_3_research_and_docx()\n"
        "                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 3 completed.'), d_res)\n"
        "                    return\n"
        "                elif 'demo 4' in q_lower_check or 'agentic demo 4' in q_lower_check:\n"
        "                    self.state_changed.emit('planning')\n"
        "                    d_res = self._demos.run_demo_4_permission_gated_execution()\n"
        "                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 4 completed.'), d_res)\n"
        "                    return\n\n"
        "                classification = self._supervisor.classify_intent(q_clean)\n"
        "                if classification.get('mode') == 'AGENTIC_WORKFLOW':\n"
        "                    print(f'[VOID Agentic] Routing {q_clean} to Multi-Agent Supervisor', flush=True)\n"
        "                    self.state_changed.emit('planning')\n"
        "                    agentic_res = self._supervisor.execute_goal(q_clean)\n"
        "                    self._handle_agentic_response(query, agentic_res.get('summary_text', 'Agentic workflow complete.'), agentic_res)\n"
        "                    return\n\n"
        + old_split_anchor
    )
    if old_split_anchor not in content:
        raise ValueError("Could not find old_split_anchor in void-widget.py")
    content = content.replace(old_split_anchor, new_interception, 1)

    # 8. VoidMiniWidget.__init__ signal connection
    old_widget_conn_anchor = "        self._engine.terminate_requested.connect(self._on_terminate)"
    new_widget_conn = (
        old_widget_conn_anchor + "\n"
        "        self._engine.agentic_update.connect(self._on_agentic_update)"
    )
    if old_widget_conn_anchor not in content:
        raise ValueError("Could not find old_widget_conn_anchor in void-widget.py")
    content = content.replace(old_widget_conn_anchor, new_widget_conn, 1)

    # 9. VoidMiniWidget._setup_ui mount AgentActivityCard
    old_card_mount_anchor = (
        "        # Response Output Card\n"
        "        self._resp_frame = QFrame(self._expanded_box)"
    )
    new_card_mount = (
        "        # Agent Activity Card (Multi-Agent Observability)\n"
        "        perm_manager = getattr(self._engine._supervisor, 'perm_mgr', None) if hasattr(self._engine, '_supervisor') and self._engine._supervisor else None\n"
        "        self._agent_card = AgentActivityCard(perm_manager, self._expanded_box)\n"
        "        self._agent_card.setVisible(False)\n"
        "        exp_layout.addWidget(self._agent_card)\n\n"
        + old_card_mount_anchor
    )
    if old_card_mount_anchor not in content:
        raise ValueError("Could not find old_card_mount_anchor in void-widget.py")
    content = content.replace(old_card_mount_anchor, new_card_mount, 1)

    # 10. Quick Chips update
    old_chips_anchor = '            ("🌐 Open Chrome", "open chromium"),'
    new_chips = (
        old_chips_anchor + '\n'
        '            ("🤖 Multi-Agent", "run agentic demo 1"),'
    )
    if old_chips_anchor not in content:
        raise ValueError("Could not find old_chips_anchor in void-widget.py")
    content = content.replace(old_chips_anchor, new_chips, 1)

    # 11. VoidMiniWidget._on_state_changed extensions
    old_state_changed_anchor = (
        '        elif state == "celebrate":\n'
        '            self._status_dot.setStyleSheet("color: #10b981; font-size: 10px;")\n'
        '            self._status_pill.setText("Celebration • Nailed it! 🎉")\n'
        '        else:  # idle'
    )
    new_state_changed = (
        '        elif state == "celebrate":\n'
        '            self._status_dot.setStyleSheet("color: #10b981; font-size: 10px;")\n'
        '            self._status_pill.setText("Celebration • Nailed it! 🎉")\n'
        '        elif state == "planning":\n'
        '            self._stop_btn.setVisible(True)\n'
        '            self._mic_btn.setVisible(False)\n'
        '            self._status_dot.setStyleSheet("color: #c084fc; font-size: 10px;")\n'
        '            self._status_pill.setText("Multi-Agent Planning... 🧭")\n'
        '        elif state == "verifying":\n'
        '            self._stop_btn.setVisible(True)\n'
        '            self._mic_btn.setVisible(False)\n'
        '            self._status_dot.setStyleSheet("color: #facc15; font-size: 10px;")\n'
        '            self._status_pill.setText("Verifying Artifacts... 🛡️")\n'
        '        elif state == "recovering":\n'
        '            self._stop_btn.setVisible(True)\n'
        '            self._mic_btn.setVisible(False)\n'
        '            self._status_dot.setStyleSheet("color: #fb923c; font-size: 10px;")\n'
        '            self._status_pill.setText("Dynamic Recovery... 🔧")\n'
        '        elif state == "waiting_approval":\n'
        '            self._stop_btn.setVisible(True)\n'
        '            self._mic_btn.setVisible(False)\n'
        '            self._status_dot.setStyleSheet("color: #f43f5e; font-size: 10px;")\n'
        '            self._status_pill.setText("Awaiting User Approval 🛑")\n'
        '        else:  # idle'
    )
    if old_state_changed_anchor not in content:
        raise ValueError("Could not find old_state_changed_anchor in void-widget.py")
    content = content.replace(old_state_changed_anchor, new_state_changed, 1)

    # 12. Add _on_agentic_update in VoidMiniWidget
    old_widget_end_anchor = "    def _on_terminate(self) -> None:"
    new_widget_handler = (
        "    def _on_agentic_update(self, state, plan, current_task) -> None:\n"
        "        if hasattr(self, '_agent_card'):\n"
        "            self._agent_card.setVisible(True)\n"
        "            self.set_expanded(True)\n"
        "            self._agent_card.update_state(state, plan, current_task)\n\n"
        + old_widget_end_anchor
    )
    if old_widget_end_anchor not in content:
        raise ValueError("Could not find old_widget_end_anchor in void-widget.py")
    content = content.replace(old_widget_end_anchor, new_widget_handler, 1)

    # Write patched file
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched content written to target file.")

    # Syntax compile check
    print("Compiling target file with py_compile...")
    py_compile.compile(str(TARGET_FILE), doraise=True)
    print("SUCCESS: void-widget.py compiled without syntax errors!")

if __name__ == "__main__":
    try:
        apply_patch()
    except Exception as e:
        print(f"FAILED to apply patch: {e}", file=sys.stderr)
        if BACKUP_FILE.exists():
            shutil.copy2(BACKUP_FILE, TARGET_FILE)
            print("Restored original file from backup.")
        sys.exit(1)

