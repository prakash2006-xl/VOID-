"""
VOID Agentic OS - Agentic UI Components
Provides frosted-glass visual components for multi-agent observability:
1. Live execution timeline (Planning -> Delegating -> Executing -> Verifying -> Completed)
2. Agent activity badges and active task display
3. Collapsible per-task progress tree
4. Interactive approval dialogue for Level 3 actions
Compatible with both PySide6 and PyQt6.
"""

from typing import Optional, Dict, Any, List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QFrame,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
    )
    from PySide6.QtCore import Qt, Signal
    SignalClass = Signal
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QWidget,
            QFrame,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QScrollArea,
        )
        from PyQt6.QtCore import Qt, pyqtSignal
        SignalClass = pyqtSignal
    except ImportError:
        # Headless stub fallback
        QWidget = object
        QFrame = object
        QVBoxLayout = object
        QHBoxLayout = object
        QLabel = object
        QPushButton = object
        QScrollArea = object
        Qt = object
        SignalClass = None

from agentic.types import (
    AgentRole,
    WorkflowLifecycleState,
    TaskStatus,
    WorkflowPlan,
    AgentTask,
)
from agentic.permissions import PermissionManager


class AgentActivityCard(QFrame):
    """
    Frosted-glass card displaying real-time multi-agent workflow progress,
    active agent assignments, verification checkpoints, and approval controls.
    """

    if SignalClass:
        approval_resolved = SignalClass(str, bool)  # request_id, approved

    def __init__(self, permission_manager: Optional[PermissionManager] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.perm_mgr = permission_manager
        self.active_request_id: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("AgentActivityCard")
        self.setStyleSheet("""
            #AgentActivityCard {
                background: rgba(15, 23, 42, 0.90);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 1. Header: Role Badge + Lifecycle State
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        self._agent_badge = QLabel("🤖 Supervisor", self)
        self._agent_badge.setStyleSheet("""
            QLabel {
                color: #38bdf8;
                font-size: 10px;
                font-weight: bold;
                background: rgba(56, 189, 248, 0.2);
                border: 1px solid rgba(56, 189, 248, 0.45);
                border-radius: 5px;
                padding: 2px 7px;
            }
        """)
        header_row.addWidget(self._agent_badge)

        self._lifecycle_badge = QLabel("IDLE", self)
        self._lifecycle_badge.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 10px;
                font-weight: bold;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 5px;
                padding: 2px 6px;
            }
        """)
        header_row.addWidget(self._lifecycle_badge)
        header_row.addStretch()

        self._duration_label = QLabel("0.0s", self)
        self._duration_label.setStyleSheet("color: #64748b; font-size: 10px;")
        header_row.addWidget(self._duration_label)
        layout.addLayout(header_row)

        # 2. Current Task Headline
        self._task_headline = QLabel("Awaiting agentic workflow...", self)
        self._task_headline.setWordWrap(True)
        self._task_headline.setStyleSheet("color: #f8fafc; font-size: 11px; font-weight: 500;")
        layout.addWidget(self._task_headline)

        # 3. Step Progress Timeline Bar
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(3)
        self.stage_labels = {}
        for stage in ["Plan", "Delegate", "Execute", "Verify", "Done"]:
            lbl = QLabel(stage, self)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                QLabel {
                    color: #475569;
                    font-size: 9px;
                    font-weight: bold;
                    background: rgba(255, 255, 255, 0.04);
                    border-radius: 4px;
                    padding: 2px 4px;
                }
            """)
            timeline_row.addWidget(lbl, stretch=1)
            self.stage_labels[stage] = lbl
        layout.addLayout(timeline_row)

        # 4. Scrollable Task Sub-Tree
        self._task_list_widget = QWidget(self)
        self._task_list_layout = QVBoxLayout(self._task_list_widget)
        self._task_list_layout.setContentsMargins(0, 2, 0, 2)
        self._task_list_layout.setSpacing(3)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setMaximumHeight(120)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll.setWidget(self._task_list_widget)
        layout.addWidget(self._scroll)

        # 5. Interactive Approval Panel (Hidden by default)
        self._approval_panel = QFrame(self)
        self._approval_panel.setVisible(False)
        self._approval_panel.setStyleSheet("""
            QFrame {
                background: rgba(245, 158, 11, 0.2);
                border: 1px solid rgba(245, 158, 11, 0.5);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        approval_layout = QVBoxLayout(self._approval_panel)
        approval_layout.setContentsMargins(6, 4, 6, 4)
        approval_layout.setSpacing(4)

        self._approval_text = QLabel("Action requires user authorization", self._approval_panel)
        self._approval_text.setStyleSheet("color: #fef08a; font-size: 10px; font-weight: bold;")
        self._approval_text.setWordWrap(True)
        approval_layout.addWidget(self._approval_text)

        app_btn_row = QHBoxLayout()
        app_btn_row.setSpacing(6)

        self._btn_approve = QPushButton("✓ Approve Action", self._approval_panel)
        self._btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_approve.setStyleSheet("""
            QPushButton {
                background: rgba(16, 185, 129, 0.35);
                color: #a7f3d0;
                border: 1px solid rgba(16, 185, 129, 0.6);
                border-radius: 5px;
                font-size: 10px;
                font-weight: bold;
                padding: 3px 8px;
            }
            QPushButton:hover { background: rgba(16, 185, 129, 0.65); color: #ffffff; }
        """)
        self._btn_approve.clicked.connect(self._on_approve_clicked)
        app_btn_row.addWidget(self._btn_approve)

        self._btn_deny = QPushButton("✕ Deny", self._approval_panel)
        self._btn_deny.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_deny.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.3);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.5);
                border-radius: 5px;
                font-size: 10px;
                font-weight: bold;
                padding: 3px 8px;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.6); color: #ffffff; }
        """)
        self._btn_deny.clicked.connect(self._on_deny_clicked)
        app_btn_row.addWidget(self._btn_deny)

        approval_layout.addLayout(app_btn_row)
        layout.addWidget(self._approval_panel)

    def update_state(
        self,
        state: WorkflowLifecycleState,
        plan: Optional[WorkflowPlan] = None,
        current_task: Optional[AgentTask] = None,
    ):
        """Refreshes UI according to orchestrator lifecycle and active task."""
        # 1. Update lifecycle badge
        self._lifecycle_badge.setText(state.value.upper())

        state_colors = {
            WorkflowLifecycleState.PLANNING: ("#c084fc", "rgba(192, 132, 252, 0.25)"),
            WorkflowLifecycleState.DELEGATING: ("#38bdf8", "rgba(56, 189, 248, 0.25)"),
            WorkflowLifecycleState.EXECUTING: ("#34d399", "rgba(52, 211, 153, 0.25)"),
            WorkflowLifecycleState.VERIFYING: ("#facc15", "rgba(250, 204, 21, 0.25)"),
            WorkflowLifecycleState.RECOVERING: ("#fb923c", "rgba(251, 146, 60, 0.25)"),
            WorkflowLifecycleState.WAITING_APPROVAL: ("#f43f5e", "rgba(244, 63, 94, 0.25)"),
            WorkflowLifecycleState.COMPLETED: ("#10b981", "rgba(16, 185, 129, 0.25)"),
            WorkflowLifecycleState.FAILED: ("#ef4444", "rgba(239, 68, 68, 0.25)"),
        }

        color, bg = state_colors.get(state, ("#94a3b8", "rgba(255, 255, 255, 0.08)"))
        self._lifecycle_badge.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10px;
                font-weight: bold;
                background: {bg};
                border: 1px solid {color}66;
                border-radius: 5px;
                padding: 2px 6px;
            }}
        """)

        # 2. Update agent badge
        if current_task and current_task.assigned_agent:
            role_name = current_task.assigned_agent.value.replace("_", " ").title()
            self._agent_badge.setText(f"🤖 {role_name}")
            self._task_headline.setText(current_task.description)
        elif plan:
            self._task_headline.setText(plan.goal)

        # 3. Highlight timeline stages
        stage_order = {
            WorkflowLifecycleState.PLANNING: "Plan",
            WorkflowLifecycleState.DELEGATING: "Delegate",
            WorkflowLifecycleState.EXECUTING: "Execute",
            WorkflowLifecycleState.VERIFYING: "Verify",
            WorkflowLifecycleState.COMPLETED: "Done",
        }
        active_stage = stage_order.get(state)

        for s_name, s_lbl in self.stage_labels.items():
            if s_name == active_stage:
                s_lbl.setStyleSheet("""
                    QLabel {
                        color: #38bdf8;
                        font-size: 9px;
                        font-weight: bold;
                        background: rgba(56, 189, 248, 0.3);
                        border: 1px solid #38bdf8;
                        border-radius: 4px;
                        padding: 2px 4px;
                    }
                """)
            else:
                s_lbl.setStyleSheet("""
                    QLabel {
                        color: #475569;
                        font-size: 9px;
                        font-weight: bold;
                        background: rgba(255, 255, 255, 0.04);
                        border-radius: 4px;
                        padding: 2px 4px;
                    }
                """)

        # 4. Render tasks in tree
        if plan and plan.tasks:
            # Clear previous task items
            while self._task_list_layout.count():
                child = self._task_list_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            for t in plan.tasks:
                status_icon = "⏳"
                icon_color = "#94a3b8"
                if t.status == TaskStatus.IN_PROGRESS:
                    status_icon = "⚙️"
                    icon_color = "#38bdf8"
                elif t.status == TaskStatus.COMPLETED:
                    status_icon = "✅"
                    icon_color = "#34d399"
                elif t.status == TaskStatus.FAILED:
                    status_icon = "❌"
                    icon_color = "#f87171"
                elif t.status == TaskStatus.WAITING_APPROVAL:
                    status_icon = "🛑"
                    icon_color = "#fbbf24"

                t_row = QLabel(f"{status_icon} [{t.assigned_agent.value[:4].upper()}] {t.description[:42]}", self._task_list_widget)
                t_row.setStyleSheet(f"color: {icon_color}; font-size: 10px;")
                self._task_list_layout.addWidget(t_row)

        # 5. Handle Approval Panel
        if state == WorkflowLifecycleState.WAITING_APPROVAL:
            self._approval_panel.setVisible(True)
            if self.perm_mgr:
                pending = self.perm_mgr.get_all_pending()
                if pending:
                    req = pending[0]
                    self.active_request_id = req.request_id
                    self._approval_text.setText(f"Approval Required:\n{req.description} ({req.tool_name})")
        else:
            self._approval_panel.setVisible(False)

    def _on_approve_clicked(self):
        if self.active_request_id and self.perm_mgr:
            self.perm_mgr.confirm_approval(self.active_request_id)
            if hasattr(self, "approval_resolved"):
                self.approval_resolved.emit(self.active_request_id, True)
            self._approval_panel.setVisible(False)

    def _on_deny_clicked(self):
        if self.active_request_id and self.perm_mgr:
            self.perm_mgr.reject_approval(self.active_request_id)
            if hasattr(self, "approval_resolved"):
                self.approval_resolved.emit(self.active_request_id, False)
            self._approval_panel.setVisible(False)
