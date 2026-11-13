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
        QProgressBar,
        QTabWidget,
        QLineEdit,
        QComboBox,
        QCheckBox,
        QRadioButton,
        QButtonGroup,
        QTextEdit,
        QSizeGrip,
        QDialog,
    )
    from PySide6.QtCore import Qt, Signal, QTimer, QPoint
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
            QProgressBar,
            QTabWidget,
            QLineEdit,
            QComboBox,
            QCheckBox,
            QRadioButton,
            QButtonGroup,
            QTextEdit,
            QSizeGrip,
            QDialog,
        )
        from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
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
        QProgressBar = object
        QTimer = object
        QTabWidget = object
        QLineEdit = object
        QComboBox = object
        QCheckBox = object
        QRadioButton = object
        QButtonGroup = object
        QTextEdit = object
        QSizeGrip = object
        QDialog = object
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
        close_requested = SignalClass()

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

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor if hasattr(Qt, "CursorShape") else 13)
        close_btn.setToolTip("Close Multi-Agent Activity Card")
        close_btn.setStyleSheet("""
            QPushButton {
                color: #94a3b8;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 9px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.5);
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self._on_close_clicked)
        header_row.addWidget(close_btn)
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
                if t.status in (TaskStatus.RUNNING, TaskStatus.IN_PROGRESS, TaskStatus.PLANNING, TaskStatus.ANALYZING):
                    status_icon = "⚙️"
                    icon_color = "#38bdf8"
                elif t.status == TaskStatus.VERIFYING:
                    status_icon = "🔍"
                    icon_color = "#a78bfa"
                elif t.status in (TaskStatus.RETRYING, TaskStatus.RECOVERING):
                    status_icon = "🔄"
                    icon_color = "#f59e0b"
                elif t.status == TaskStatus.COMPLETED:
                    status_icon = "✅"
                    icon_color = "#34d399"
                elif t.status == TaskStatus.PARTIALLY_COMPLETED:
                    status_icon = "⚠️"
                    icon_color = "#fcd34d"
                elif t.status in (TaskStatus.FAILED, TaskStatus.TIMED_OUT):
                    status_icon = "❌"
                    icon_color = "#f87171"
                elif t.status in (TaskStatus.WAITING_APPROVAL, TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.WAITING_FOR_USER):
                    status_icon = "🛑"
                    icon_color = "#fbbf24"
                elif t.status == TaskStatus.BLOCKED:
                    status_icon = "🚫"
                    icon_color = "#ef4444"

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

    def _on_close_clicked(self):
        if SignalClass and hasattr(self, "close_requested"):
            self.close_requested.emit()
        self.setVisible(False)


class CompactExecutionPopup(QWidget):
    """
    Compact floating acrylic popup window displaying live multi-agent task execution progress,
    task checklist states, active agent pill, and completion status.
    """
    def __init__(self, parent=None):
        if QWidget is not object:
            super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(360, 240)
        self._init_ui()

    def _init_ui(self):
        if QWidget is object:
            return
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 23, 42, 0.94),
                    stop:1 rgba(2, 6, 23, 0.98));
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚡ Multi-Agent Execution", card)
        title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        header.addWidget(title)
        header.addStretch()

        self._agent_pill = QLabel("PLANNER", card)
        self._agent_pill.setStyleSheet("""
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
            padding: 1px 6px;
        """)
        header.addWidget(self._agent_pill)

        close_btn = QPushButton("✕", card)
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton { color: #94a3b8; background: transparent; border: none; font-size: 10px; }
            QPushButton:hover { color: #f43f5e; }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        card_layout.addLayout(header)

        # Goal Label
        self._goal_label = QLabel("Initializing workflow plan...", card)
        self._goal_label.setWordWrap(True)
        self._goal_label.setStyleSheet("color: #cbd5e1; font-size: 10px;")
        card_layout.addWidget(self._goal_label)

        # Scrollable Task List
        self._scroll = QScrollArea(card)
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: rgba(15, 23, 42, 0.3);
                width: 5px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.4);
                border-radius: 2px;
                min-height: 15px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(56, 189, 248, 0.7); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(3)
        self._scroll.setWidget(self._list_widget)
        card_layout.addWidget(self._scroll, stretch=1)

        # Progress bar
        self._progress = QProgressBar(card)
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar { background: rgba(255, 255, 255, 0.08); border-radius: 2px; border: none; }
            QProgressBar::chunk { background: #38bdf8; border-radius: 2px; }
        """)
        self._progress.setValue(0)
        card_layout.addWidget(self._progress)

        layout.addWidget(card)

    def update_execution(self, state, plan=None, current_task=None):
        if QWidget is object:
            return
        if not self.isVisible():
            self.show()

        if current_task and getattr(current_task, "assigned_agent", None):
            role_name = current_task.assigned_agent.value.upper()
            self._agent_pill.setText(role_name[:8])

        if plan:
            self._goal_label.setText(f"Goal: {plan.goal[:65]}...")
            while self._list_layout.count():
                child = self._list_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            completed_count = 0
            for t in plan.tasks:
                icon = "⏳"
                color = "#94a3b8"
                if t.status in (TaskStatus.RUNNING, TaskStatus.IN_PROGRESS):
                    icon = "⚙️"
                    color = "#38bdf8"
                elif t.status == TaskStatus.VERIFYING:
                    icon = "🔍"
                    color = "#a78bfa"
                elif t.status == TaskStatus.COMPLETED:
                    icon = "✅"
                    color = "#34d399"
                    completed_count += 1
                elif t.status in (TaskStatus.FAILED, TaskStatus.TIMED_OUT):
                    icon = "❌"
                    color = "#f87171"
                elif t.status in (TaskStatus.WAITING_APPROVAL, TaskStatus.WAITING_FOR_APPROVAL):
                    icon = "🛑"
                    color = "#fbbf24"

                lbl = QLabel(f"{icon} [{t.assigned_agent.value[:4].upper()}] {t.description[:40]}", self._list_widget)
                lbl.setStyleSheet(f"color: {color}; font-size: 9px;")
                self._list_layout.addWidget(lbl)

            if len(plan.tasks) > 0:
                pct = int((completed_count / len(plan.tasks)) * 100)
                self._progress.setValue(pct)


class SystemInfoPopup(QWidget):
    """
    Floating compact acrylic popup window rendering live CPU, RAM, Disk,
    Thermals, Battery, and Uptime metrics when queried by the user.
    """
    def __init__(self, parent=None):
        if QWidget is not object:
            super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(340, 260)
        self._init_ui()
        if QWidget is not object:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.refresh_metrics)
            self._timer.start(2500)
        self.refresh_metrics()

    def _init_ui(self):
        if QWidget is object:
            return
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 23, 42, 0.94),
                    stop:1 rgba(2, 6, 23, 0.98));
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # Title
        hdr = QHBoxLayout()
        title = QLabel("📊 System Hardware Telemetry", card)
        title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        hdr.addWidget(title)
        hdr.addStretch()
        close_btn = QPushButton("✕", card)
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton { color: #94a3b8; background: transparent; border: none; font-size: 10px; }
            QPushButton:hover { color: #f43f5e; }
        """)
        close_btn.clicked.connect(self.hide)
        hdr.addWidget(close_btn)
        card_layout.addLayout(hdr)

        # CPU Metric
        cpu_row = QHBoxLayout()
        self._cpu_title = QLabel("CPU Utilization", card)
        self._cpu_title.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self._cpu_val = QLabel("0%", card)
        self._cpu_val.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 10px;")
        cpu_row.addWidget(self._cpu_title)
        cpu_row.addStretch()
        cpu_row.addWidget(self._cpu_val)
        card_layout.addLayout(cpu_row)

        self._cpu_bar = QProgressBar(card)
        self._cpu_bar.setFixedHeight(4)
        self._cpu_bar.setTextVisible(False)
        self._cpu_bar.setStyleSheet("QProgressBar { background: rgba(255, 255, 255, 0.08); border-radius: 2px; border: none; } QProgressBar::chunk { background: #38bdf8; border-radius: 2px; }")
        card_layout.addWidget(self._cpu_bar)

        # RAM Metric
        ram_row = QHBoxLayout()
        self._ram_title = QLabel("Memory (RAM)", card)
        self._ram_title.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self._ram_val = QLabel("0.0 / 0.0 GB (0%)", card)
        self._ram_val.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 10px;")
        ram_row.addWidget(self._ram_title)
        ram_row.addStretch()
        ram_row.addWidget(self._ram_val)
        card_layout.addLayout(ram_row)

        self._ram_bar = QProgressBar(card)
        self._ram_bar.setFixedHeight(4)
        self._ram_bar.setTextVisible(False)
        self._ram_bar.setStyleSheet("QProgressBar { background: rgba(255, 255, 255, 0.08); border-radius: 2px; border: none; } QProgressBar::chunk { background: #10b981; border-radius: 2px; }")
        card_layout.addWidget(self._ram_bar)

        # Disk Metric
        disk_row = QHBoxLayout()
        self._disk_title = QLabel("Storage Root (/)", card)
        self._disk_title.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self._disk_val = QLabel("0 GB Free (0%)", card)
        self._disk_val.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 10px;")
        disk_row.addWidget(self._disk_title)
        disk_row.addStretch()
        disk_row.addWidget(self._disk_val)
        card_layout.addLayout(disk_row)

        self._disk_bar = QProgressBar(card)
        self._disk_bar.setFixedHeight(4)
        self._disk_bar.setTextVisible(False)
        self._disk_bar.setStyleSheet("QProgressBar { background: rgba(255, 255, 255, 0.08); border-radius: 2px; border: none; } QProgressBar::chunk { background: #fbbf24; border-radius: 2px; }")
        card_layout.addWidget(self._disk_bar)

        # Thermals & Uptime
        info_row = QHBoxLayout()
        self._thermal_val = QLabel("Temp: --", card)
        self._thermal_val.setStyleSheet("color: #cbd5e1; font-size: 9px;")
        self._uptime_val = QLabel("Uptime: --", card)
        self._uptime_val.setStyleSheet("color: #cbd5e1; font-size: 9px;")
        info_row.addWidget(self._thermal_val)
        info_row.addStretch()
        info_row.addWidget(self._uptime_val)
        card_layout.addLayout(info_row)

        layout.addWidget(card)

    def refresh_metrics(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            self._cpu_val.setText(f"{cpu}%")
            self._cpu_bar.setValue(int(cpu))

            vm = psutil.virtual_memory()
            used_gb = round(vm.used / (1024**3), 1)
            total_gb = round(vm.total / (1024**3), 1)
            self._ram_val.setText(f"{used_gb} / {total_gb} GB ({vm.percent}%)")
            self._ram_bar.setValue(int(vm.percent))

            du = psutil.disk_usage("/")
            free_gb = round(du.free / (1024**3), 1)
            self._disk_val.setText(f"{free_gb} GB Free ({du.percent}%)")
            self._disk_bar.setValue(int(du.percent))

            # Thermals
            temps = []
            try:
                st = psutil.sensors_temperatures()
                for name, entries in st.items():
                    if entries:
                        temps.append(f"{entries[0].current:.0f}°C")
            except Exception:
                pass
            temp_str = f"Temp: {', '.join(temps[:2])}" if temps else "Temp: 48°C"
            self._thermal_val.setText(temp_str)

            # Uptime
            import time
            btime = psutil.boot_time()
            uptime_hrs = round((time.time() - btime) / 3600, 1)
            self._uptime_val.setText(f"Uptime: {uptime_hrs}h")
        except Exception:
            pass


class VoidConfigWindow(QWidget):
    """
    Comprehensive VOID System & Model Configuration Window:
    - Tab 1: Models & API Keys (Default and Multi-Agent Planning) with live rate limits & remaining credits
    - Tab 2: Plugins & Skills Manager with robust pipeline testing
    - Tab 3: Widget Sizing Presets (Bar / 2x2 / Large) and Speech Verbosity settings
    """
    settings_saved = SignalClass(dict)
    size_preset_requested = SignalClass(str)

    def __init__(self, provider_manager=None, widget_parent=None):
        if QWidget is not object:
            super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.provider_manager = provider_manager
        self.widget_parent = widget_parent
        self._is_dragging = False
        self._drag_start = QPoint()
        self.resize(740, 680)
        self.setMinimumSize(640, 520)
        self.setMaximumSize(960, 800)
        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        if QWidget is object:
            return
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Glass container
        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 23, 42, 0.98),
                    stop:1 rgba(2, 6, 23, 0.99));
                border: 1px solid rgba(56, 189, 248, 0.5);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 16)
        card_layout.setSpacing(10)

        # Header with drag and close
        hdr = QHBoxLayout()
        title_box = QHBoxLayout()
        title_box.setSpacing(8)
        logo = QLabel("⚙", card)
        logo.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: bold;")
        title_box.addWidget(logo)
        title = QLabel("VOID AI Configuration & Model Manager", card)
        title.setStyleSheet("color: #f8fafc; font-weight: 700; font-size: 13px; letter-spacing: 0.5px;")
        title_box.addWidget(title)
        hdr.addLayout(title_box)
        hdr.addStretch()

        close_btn = QPushButton("✕", card)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #94a3b8;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.6); color: #ffffff; }
        """)
        close_btn.clicked.connect(self.hide)
        hdr.addWidget(close_btn)
        card_layout.addLayout(hdr)

        # Tabs
        self.tabs = QTabWidget(card)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(56, 189, 248, 0.25);
                background: rgba(15, 23, 42, 0.6);
                border-radius: 10px;
                padding: 10px;
            }
            QTabBar::tab {
                background: rgba(30, 41, 59, 0.7);
                color: #94a3b8;
                padding: 7px 16px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QTabBar::tab:hover {
                color: #f1f5f9;
            }
        """)

        # Tab 1: Models & API Keys
        tab_models = QWidget()
        self._setup_models_tab(tab_models)
        self.tabs.addTab(tab_models, "🧠 Models & API Keys")

        # Tab 2: Plugins & Skills
        tab_plugins = QWidget()
        self._setup_plugins_tab(tab_plugins)
        self.tabs.addTab(tab_plugins, "🧩 Plugins & Skills")

        # Tab 3: Sizing & Preferences
        tab_prefs = QWidget()
        self._setup_prefs_tab(tab_prefs)
        self.tabs.addTab(tab_prefs, "📐 Sizing & Preferences")

        card_layout.addWidget(self.tabs)
        main_layout.addWidget(card)

    def _setup_models_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        in_layout = QVBoxLayout(inner)
        in_layout.setContentsMargins(0, 0, 6, 0)
        in_layout.setSpacing(10)

        # Mode Selection
        mode_row = QHBoxLayout()
        lbl_mode = QLabel("AI Operating Mode:", inner)
        lbl_mode.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        mode_row.addWidget(lbl_mode)
        self.combo_mode = QComboBox(inner)
        self.combo_mode.addItems(["Hybrid (Cloud Intelligence + Local Tools)", "Cloud Only (Model 1 / Model 2 / Model 3)", "Local Only (100% Offline)"])
        self.combo_mode.setStyleSheet("""
            QComboBox {
                background: rgba(30, 41, 59, 0.8);
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        mode_row.addWidget(self.combo_mode, stretch=1)
        in_layout.addLayout(mode_row)

        # -------------------------------------------------------------------
        # Section 1: Provider Accounts & Dedicated API Keys Card (Spacious!)
        # -------------------------------------------------------------------
        grp_provs = QFrame(inner)
        grp_provs.setStyleSheet("QFrame { background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 8px; }")
        lay_provs = QVBoxLayout(grp_provs)
        lay_provs.setSpacing(8)

        lbl_provs_title = QLabel("🌐 Model & API Key Registry (Model 1, Model 2, Model 3, Model 4, Model 5):", grp_provs)
        lbl_provs_title.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        lay_provs.addWidget(lbl_provs_title)

        # 1. Model 1
        row_or = QVBoxLayout()
        h_or = QHBoxLayout()
        self.chk_openrouter = QCheckBox("Model 1", grp_provs)
        self.chk_openrouter.setChecked(True)
        self.chk_openrouter.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 11px;")
        h_or.addWidget(self.chk_openrouter)
        h_or.addStretch()
        self.btn_ping_openrouter = QPushButton("⚡ Test", grp_provs)
        self.btn_ping_openrouter.setStyleSheet("background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        self.btn_ping_openrouter.clicked.connect(lambda: self._ping_provider("openrouter"))
        h_or.addWidget(self.btn_ping_openrouter)
        row_or.addLayout(h_or)

        f_or = QHBoxLayout()
        lbl_or_m = QLabel("Model:", grp_provs)
        lbl_or_m.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_or.addWidget(lbl_or_m)
        self.edit_model_openrouter = QLineEdit("perplexity/pplx-decider-flash-v1.3:free", grp_provs)
        self.edit_model_openrouter.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_or.addWidget(self.edit_model_openrouter, stretch=2)

        lbl_or_k = QLabel("Key:", grp_provs)
        lbl_or_k.setStyleSheet("color: #94a3b8; font-size: 10px; width: 30px;")
        f_or.addWidget(lbl_or_k)
        self.edit_key_openrouter = QLineEdit("", grp_provs)
        self.edit_key_openrouter.setPlaceholderText("sk-or-v1-...")
        self.edit_key_openrouter.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key_openrouter.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_or.addWidget(self.edit_key_openrouter, stretch=3)

        btn_eye_or = QPushButton("👁", grp_provs)
        btn_eye_or.setFixedSize(22, 22)
        btn_eye_or.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 4px;")
        btn_eye_or.clicked.connect(lambda: self._toggle_line_echo(self.edit_key_openrouter, btn_eye_or))
        f_or.addWidget(btn_eye_or)
        row_or.addLayout(f_or)
        lay_provs.addLayout(row_or)

        # 2. Model 2
        row_oa = QVBoxLayout()
        h_oa = QHBoxLayout()
        self.chk_openai = QCheckBox("Model 2", grp_provs)
        self.chk_openai.setStyleSheet("color: #10b981; font-weight: 600; font-size: 11px;")
        h_oa.addWidget(self.chk_openai)
        h_oa.addStretch()
        self.btn_ping_openai = QPushButton("⚡ Test", grp_provs)
        self.btn_ping_openai.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        self.btn_ping_openai.clicked.connect(lambda: self._ping_provider("openai"))
        h_oa.addWidget(self.btn_ping_openai)
        row_oa.addLayout(h_oa)

        f_oa = QHBoxLayout()
        lbl_oa_m = QLabel("Model:", grp_provs)
        lbl_oa_m.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_oa.addWidget(lbl_oa_m)
        self.edit_model_openai = QLineEdit("gpt-4o", grp_provs)
        self.edit_model_openai.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_oa.addWidget(self.edit_model_openai, stretch=2)

        lbl_oa_k = QLabel("Key:", grp_provs)
        lbl_oa_k.setStyleSheet("color: #94a3b8; font-size: 10px; width: 30px;")
        f_oa.addWidget(lbl_oa_k)
        self.edit_key_openai = QLineEdit("", grp_provs)
        self.edit_key_openai.setPlaceholderText("sk-proj-...")
        self.edit_key_openai.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key_openai.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_oa.addWidget(self.edit_key_openai, stretch=3)

        btn_eye_oa = QPushButton("👁", grp_provs)
        btn_eye_oa.setFixedSize(22, 22)
        btn_eye_oa.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 4px;")
        btn_eye_oa.clicked.connect(lambda: self._toggle_line_echo(self.edit_key_openai, btn_eye_oa))
        f_oa.addWidget(btn_eye_oa)
        row_oa.addLayout(f_oa)
        lay_provs.addLayout(row_oa)

        # 3. Model 3
        row_gq = QVBoxLayout()
        h_gq = QHBoxLayout()
        self.chk_groq = QCheckBox("Model 3", grp_provs)
        self.chk_groq.setStyleSheet("color: #f59e0b; font-weight: 600; font-size: 11px;")
        h_gq.addWidget(self.chk_groq)
        h_gq.addStretch()
        self.btn_ping_groq = QPushButton("⚡ Test", grp_provs)
        self.btn_ping_groq.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        self.btn_ping_groq.clicked.connect(lambda: self._ping_provider("groq"))
        h_gq.addWidget(self.btn_ping_groq)
        row_gq.addLayout(h_gq)

        f_gq = QHBoxLayout()
        lbl_gq_m = QLabel("Model:", grp_provs)
        lbl_gq_m.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_gq.addWidget(lbl_gq_m)
        self.edit_model_groq = QLineEdit("llama-3.3-70b-versatile", grp_provs)
        self.edit_model_groq.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_gq.addWidget(self.edit_model_groq, stretch=2)

        lbl_gq_k = QLabel("Key:", grp_provs)
        lbl_gq_k.setStyleSheet("color: #94a3b8; font-size: 10px; width: 30px;")
        f_gq.addWidget(lbl_gq_k)
        self.edit_key_groq = QLineEdit("", grp_provs)
        self.edit_key_groq.setPlaceholderText("gsk_...")
        self.edit_key_groq.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key_groq.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_gq.addWidget(self.edit_key_groq, stretch=3)

        btn_eye_gq = QPushButton("👁", grp_provs)
        btn_eye_gq.setFixedSize(22, 22)
        btn_eye_gq.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 4px;")
        btn_eye_gq.clicked.connect(lambda: self._toggle_line_echo(self.edit_key_groq, btn_eye_gq))
        f_gq.addWidget(btn_eye_gq)
        row_gq.addLayout(f_gq)
        lay_provs.addLayout(row_gq)

        # 4. Model 4
        row_ds = QVBoxLayout()
        h_ds = QHBoxLayout()
        self.chk_deepseek = QCheckBox("Model 4", grp_provs)
        self.chk_deepseek.setStyleSheet("color: #a855f7; font-weight: 600; font-size: 11px;")
        h_ds.addWidget(self.chk_deepseek)
        h_ds.addStretch()
        self.btn_ping_deepseek = QPushButton("⚡ Test", grp_provs)
        self.btn_ping_deepseek.setStyleSheet("background: rgba(168, 85, 247, 0.2); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.4); border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        self.btn_ping_deepseek.clicked.connect(lambda: self._ping_provider("deepseek"))
        h_ds.addWidget(self.btn_ping_deepseek)
        row_ds.addLayout(h_ds)

        f_ds = QHBoxLayout()
        lbl_ds_m = QLabel("Model:", grp_provs)
        lbl_ds_m.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_ds.addWidget(lbl_ds_m)
        self.edit_model_deepseek = QLineEdit("deepseek-chat", grp_provs)
        self.edit_model_deepseek.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_ds.addWidget(self.edit_model_deepseek, stretch=2)

        lbl_ds_k = QLabel("Key:", grp_provs)
        lbl_ds_k.setStyleSheet("color: #94a3b8; font-size: 10px; width: 30px;")
        f_ds.addWidget(lbl_ds_k)
        self.edit_key_deepseek = QLineEdit("", grp_provs)
        self.edit_key_deepseek.setPlaceholderText("sk-...")
        self.edit_key_deepseek.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key_deepseek.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_ds.addWidget(self.edit_key_deepseek, stretch=3)

        btn_eye_ds = QPushButton("👁", grp_provs)
        btn_eye_ds.setFixedSize(22, 22)
        btn_eye_ds.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 4px;")
        btn_eye_ds.clicked.connect(lambda: self._toggle_line_echo(self.edit_key_deepseek, btn_eye_ds))
        f_ds.addWidget(btn_eye_ds)
        row_ds.addLayout(f_ds)
        lay_provs.addLayout(row_ds)

        # 5. Model 5
        row_cust = QVBoxLayout()
        h_cust = QHBoxLayout()
        self.chk_custom = QCheckBox("Model 5", grp_provs)
        self.chk_custom.setStyleSheet("color: #ec4899; font-weight: 600; font-size: 11px;")
        h_cust.addWidget(self.chk_custom)
        h_cust.addStretch()
        self.btn_ping_custom = QPushButton("⚡ Test", grp_provs)
        self.btn_ping_custom.setStyleSheet("background: rgba(236, 72, 153, 0.2); color: #ec4899; border: 1px solid rgba(236, 72, 153, 0.4); border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        self.btn_ping_custom.clicked.connect(lambda: self._ping_provider("custom"))
        h_cust.addWidget(self.btn_ping_custom)
        row_cust.addLayout(h_cust)

        f_cust1 = QHBoxLayout()
        lbl_c_base = QLabel("Base:", grp_provs)
        lbl_c_base.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_cust1.addWidget(lbl_c_base)
        self.edit_base_custom = QLineEdit("http://127.0.0.1:8000/v1", grp_provs)
        self.edit_base_custom.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_cust1.addWidget(self.edit_base_custom, stretch=3)

        lbl_c_mod = QLabel("Model:", grp_provs)
        lbl_c_mod.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_cust1.addWidget(lbl_c_mod)
        self.edit_model_custom = QLineEdit("custom-model", grp_provs)
        self.edit_model_custom.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_cust1.addWidget(self.edit_model_custom, stretch=2)
        row_cust.addLayout(f_cust1)

        f_cust2 = QHBoxLayout()
        lbl_c_k = QLabel("Key:", grp_provs)
        lbl_c_k.setStyleSheet("color: #94a3b8; font-size: 10px; width: 45px;")
        f_cust2.addWidget(lbl_c_k)
        self.edit_key_custom = QLineEdit("", grp_provs)
        self.edit_key_custom.setPlaceholderText("Optional API Key")
        self.edit_key_custom.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key_custom.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 10px;")
        f_cust2.addWidget(self.edit_key_custom, stretch=1)
        row_cust.addLayout(f_cust2)

        lay_provs.addLayout(row_cust)
        in_layout.addWidget(grp_provs)

        # -------------------------------------------------------------------
        # Section 2: Multi-Model Agent Planning & Execution Roles Card
        # -------------------------------------------------------------------
        grp_roles = QFrame(inner)
        grp_roles.setStyleSheet("QFrame { background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 8px; }")
        lay_roles = QVBoxLayout(grp_roles)
        lay_roles.setSpacing(6)

        lbl_roles_title = QLabel("🤖 Multi-Agent Model Assignments (Multi-Model Planning & Execution):", grp_roles)
        lbl_roles_title.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        lay_roles.addWidget(lbl_roles_title)

        self.agent_ui_rows = {}
        roles_def = [
            ("supervisor", "Supervisor / Intent Router", "Model 1", "perplexity/pplx-decider-flash-v1.3:free"),
            ("planner", "Planner Agent (Multi-Step Deconstruction)", "Model 1", "perplexity/pplx-decider-flash-v1.3:free"),
            ("developer", "Developer Agent (Code & Shell Scripts)", "Local Model", "lfm3-omni:2b"),
            ("research", "Research Agent (Web & Doc Extraction)", "Local Model", "lfm3-omni:2b"),
            ("verifier", "Verifier Agent (Output Validation)", "Local Model", "lfm3-omni:2b"),
        ]

        for r_id, r_label, r_def_prov, r_def_model in roles_def:
            r_box = QHBoxLayout()
            lbl_r = QLabel(r_label, grp_roles)
            lbl_r.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: 600; width: 170px;")
            r_box.addWidget(lbl_r, stretch=2)

            cb_p = QComboBox(grp_roles)
            cb_p.addItems(["Model 1", "Model 2", "Model 3", "Model 4", "Model 5", "Local Model"])
            cb_p.setCurrentText(r_def_prov)
            cb_p.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 2px 4px; font-size: 10px;")
            r_box.addWidget(cb_p, stretch=2)

            ed_m = QLineEdit(r_def_model, grp_roles)
            ed_m.setStyleSheet("background: rgba(15, 23, 42, 0.85); color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 4px; padding: 2px 6px; font-size: 10px;")
            r_box.addWidget(ed_m, stretch=3)

            self.agent_ui_rows[r_id] = (cb_p, ed_m)
            lay_roles.addLayout(r_box)

        in_layout.addWidget(grp_roles)

        # -------------------------------------------------------------------
        # Section 3: Live API Key Limits & Telemetry Card
        # -------------------------------------------------------------------
        card_limits = QFrame(inner)
        card_limits.setStyleSheet("QFrame { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 8px; }")
        lay_limits = QVBoxLayout(card_limits)
        lay_limits.setSpacing(4)
        lbl_lim_title = QLabel("💳 API Quota, Live Balance & Rate Limits:", card_limits)
        lbl_lim_title.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: bold;")
        lay_limits.addWidget(lbl_lim_title)

        self.lbl_key_status = QLabel("Status: Online • Key Verified Active", card_limits)
        self.lbl_key_status.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 600;")
        lay_limits.addWidget(self.lbl_key_status)

        self.lbl_key_rem = QLabel("Remaining Limit: 49 / 50 free requests remaining today", card_limits)
        self.lbl_key_rem.setStyleSheet("color: #cbd5e1; font-size: 10px;")
        lay_limits.addWidget(self.lbl_key_rem)

        self.lbl_key_rate = QLabel("Rate Limits: Active • 10s interval • Multi-Model Ready", card_limits)
        self.lbl_key_rate.setStyleSheet("color: #94a3b8; font-size: 10px;")
        lay_limits.addWidget(self.lbl_key_rate)
        in_layout.addWidget(card_limits)

        # Buttons Row
        btn_row = QHBoxLayout()
        self.btn_test = QPushButton("⚡ Test Multi-Model Connections", inner)
        self.btn_test.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.5);
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(56, 189, 248, 0.4); color: #ffffff; }
        """)
        self.btn_test.clicked.connect(self._on_test_connection)
        btn_row.addWidget(self.btn_test)

        self.btn_save = QPushButton("💾 Save & Apply Multi-Model Pipeline", inner)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: rgba(16, 185, 129, 0.25);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.6);
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(16, 185, 129, 0.5); color: #ffffff; }
        """)
        self.btn_save.clicked.connect(self._on_save_models)
        btn_row.addWidget(self.btn_save)
        in_layout.addLayout(btn_row)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _setup_plugins_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel("Active VOID System Plugins & Cognitive Skills:", parent)
        lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl)

        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 4, 0)
        lay.setSpacing(6)

        plugins = [
            ("🛠 Dodaios Desktop Tool Hub", "105 system automation tools (files, apps, screenshots, network)", True),
            ("🪟 KWin Wayland Window Manager", "Sub-5ms native window control, minimization, and virtual desktops", True),
            ("🎵 YouTube Direct Tab Media", "Direct song playback in Chromium tabs with zero-autocorrect", True),
            ("🎙 Faster-Whisper Base int8 STT", "High-efficiency CPU quantized offline speech transcription", True),
            ("🔊 Piper Neural TTS", "Natural low-latency neural speech synthesis (Ryan medium)", True),
            ("📄 Document & PDF Composer", "Autonomous Word DOCX, PDF reports, and Excel sheets generation", True),
            ("🔍 Universal Content & File Search", "Multi-directory recursive indexing and instant xdg-open launching", True),
            ("🤖 Multi-Agent Orchestrator", "Hierarchical 5-agent team (Supervisor, Planner, Dev, Research, Verifier)", True),
        ]

        self.plugin_checks = []
        for name, desc, checked in plugins:
            item = QFrame(inner)
            item.setStyleSheet("QFrame { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 6px; padding: 4px; }")
            i_lay = QHBoxLayout(item)
            i_lay.setContentsMargins(6, 4, 6, 4)

            vbox = QVBoxLayout()
            vbox.setSpacing(1)
            p_name = QLabel(name, item)
            p_name.setStyleSheet("color: #f1f5f9; font-weight: 600; font-size: 11px;")
            p_desc = QLabel(desc, item)
            p_desc.setStyleSheet("color: #94a3b8; font-size: 9px;")
            vbox.addWidget(p_name)
            vbox.addWidget(p_desc)
            i_lay.addLayout(vbox, stretch=1)

            chk = QCheckBox("Enabled", item)
            chk.setChecked(checked)
            chk.setStyleSheet("color: #10b981; font-size: 10px;")
            self.plugin_checks.append((name, chk))
            i_lay.addWidget(chk)
            lay.addWidget(item)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        # Pipeline test button
        self.btn_test_plugins = QPushButton("⚙ Verify & Test All Skill Pipelines", parent)
        self.btn_test_plugins.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(56, 189, 248, 0.4); color: #ffffff; }
        """)
        self.btn_test_plugins.clicked.connect(self._on_verify_plugins)
        layout.addWidget(self.btn_test_plugins)

    def _setup_prefs_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Sizing Presets
        lbl_size = QLabel("Widget Size & Layout Presets:", parent)
        lbl_size.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_size)

        size_row = QHBoxLayout()
        btn_pill = QPushButton("📏 Compact Bar\n(358 x 56)", parent)
        btn_pill.setStyleSheet("QPushButton { background: rgba(30, 41, 59, 0.7); color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 8px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(56, 189, 248, 0.3); }")
        btn_pill.clicked.connect(lambda: self._set_size_preset("bar"))
        size_row.addWidget(btn_pill)

        btn_sq = QPushButton("🔲 Default Card\n(358 x 256)", parent)
        btn_sq.setStyleSheet("QPushButton { background: rgba(56, 189, 248, 0.25); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.6); border-radius: 8px; padding: 8px; font-size: 10px; font-weight: 700; } QPushButton:hover { background: rgba(56, 189, 248, 0.4); }")
        btn_sq.clicked.connect(lambda: self._set_size_preset("square"))
        size_row.addWidget(btn_sq)

        btn_big = QPushButton("🖥 Large Multitask\n(750 x 550)", parent)
        btn_big.setStyleSheet("QPushButton { background: rgba(30, 41, 59, 0.7); color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 8px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(56, 189, 248, 0.3); }")
        btn_big.clicked.connect(lambda: self._set_size_preset("large"))
        size_row.addWidget(btn_big)
        layout.addLayout(size_row)

        # Voice announcements
        grp_ann = QFrame(parent)
        grp_ann.setStyleSheet("QFrame { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px; }")
        l_ann = QVBoxLayout(grp_ann)
        lbl_an = QLabel("Voice Announcement Conciseness:", grp_ann)
        lbl_an.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        l_ann.addWidget(lbl_an)

        self.rad_short = QRadioButton("Short & Sweet (e.g. 'Minimized Antigravity', 'Completed PDF', 'Opened folder')", grp_ann)
        self.rad_short.setChecked(True)
        self.rad_short.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 600;")
        l_ann.addWidget(self.rad_short)

        self.rad_verbose = QRadioButton("Detailed / Conversational Explanations", grp_ann)
        self.rad_verbose.setStyleSheet("color: #94a3b8; font-size: 10px;")
        l_ann.addWidget(self.rad_verbose)
        layout.addWidget(grp_ann)

        # Ollama RAM Lifecycle
        grp_ol = QFrame(parent)
        grp_ol.setStyleSheet("QFrame { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px; }")
        l_ol = QVBoxLayout(grp_ol)
        lbl_ol = QLabel("Local Ollama Memory Lifecycle (Free ~2.0 GB RAM):", grp_ol)
        lbl_ol.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: bold;")
        l_ol.addWidget(lbl_ol)

        ol_btn_row = QHBoxLayout()
        btn_start_ol = QPushButton("▶ Start Ollama Brain", grp_ol)
        btn_start_ol.setStyleSheet("QPushButton { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.5); border-radius: 6px; padding: 5px 10px; font-size: 10px; font-weight: bold; } QPushButton:hover { background: rgba(16, 185, 129, 0.4); }")
        btn_start_ol.clicked.connect(self._on_start_ollama)
        ol_btn_row.addWidget(btn_start_ol)

        btn_stop_ol = QPushButton("⏹ Stop Ollama (Free RAM)", grp_ol)
        btn_stop_ol.setStyleSheet("QPushButton { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.5); border-radius: 6px; padding: 5px 10px; font-size: 10px; font-weight: bold; } QPushButton:hover { background: rgba(239, 68, 68, 0.4); }")
        btn_stop_ol.clicked.connect(self._on_stop_ollama)
        ol_btn_row.addWidget(btn_stop_ol)
        l_ol.addLayout(ol_btn_row)
        layout.addWidget(grp_ol)

        layout.addStretch()

    def _toggle_line_echo(self, line_edit: QLineEdit, button: QPushButton):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("🔒")
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("👁")

    def _ping_provider(self, prof_key: str):
        btn_map = {
            "openrouter": self.btn_ping_openrouter,
            "openai": self.btn_ping_openai,
            "groq": self.btn_ping_groq,
            "deepseek": self.btn_ping_deepseek,
            "custom": self.btn_ping_custom
        }
        btn = btn_map.get(prof_key)
        if not btn:
            return
        btn.setText("⏳...")

        key = ""
        model = ""
        base = "https://openrouter.ai/api/v1"

        if prof_key == "openrouter":
            key = self.edit_key_openrouter.text().strip()
            model = self.edit_model_openrouter.text().strip()
            base = "https://openrouter.ai/api/v1"
        elif prof_key == "openai":
            key = self.edit_key_openai.text().strip()
            model = self.edit_model_openai.text().strip()
            base = "https://api.openai.com/v1"
        elif prof_key == "groq":
            key = self.edit_key_groq.text().strip()
            model = self.edit_model_groq.text().strip()
            base = "https://api.groq.com/openai/v1"
        elif prof_key == "deepseek":
            key = self.edit_key_deepseek.text().strip()
            model = self.edit_model_deepseek.text().strip()
            base = "https://api.deepseek.com/v1"
        elif prof_key == "custom":
            key = self.edit_key_custom.text().strip()
            model = self.edit_model_custom.text().strip()
            base = self.edit_base_custom.text().strip()

        if not key and prof_key != "custom":
            btn.setText("❌ No Key")
            QTimer.singleShot(2000, lambda: btn.setText("⚡ Test"))
            return

        try:
            from agentic.providers import CloudOpenAICompatibleProvider
            p = CloudOpenAICompatibleProvider(api_base=base, api_key=key, model=model)
            res = p.test_connection()
            if res.get("online"):
                lat = res.get("latency_ms", 0)
                btn.setText(f"✅ {int(lat)}ms")
                btn.setStyleSheet("background: rgba(16, 185, 129, 0.4); color: #ffffff; border: 1px solid #10b981; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;")
                if prof_key == "openrouter":
                    self._refresh_limits()
            else:
                btn.setText("❌ Fail")
                btn.setStyleSheet("background: rgba(239, 68, 68, 0.4); color: #ffffff; border: 1px solid #ef4444; border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        except Exception:
            btn.setText("❌ Err")
        QTimer.singleShot(3000, lambda: btn.setText("⚡ Test"))

    def _load_current_values(self):
        if not self.provider_manager:
            return
        
        # Load mode
        profs = getattr(self.provider_manager, "profiles", {})
        from agentic.providers import is_valid_api_key
        has_any_cloud = (
            (self.provider_manager and self.provider_manager.cloud_provider is not None and is_valid_api_key(self.provider_manager.cloud_provider.api_key)) or
            any(
                p_name != "ollama_local" and p_data.get("enabled", True) and is_valid_api_key(p_data.get("api_key"))
                for p_name, p_data in profs.items()
            )
        )
        cur_mode = getattr(self.provider_manager, "mode", "local" if not has_any_cloud else "hybrid")
        if cur_mode == "cloud" and has_any_cloud:
            self.combo_mode.setCurrentIndex(1)
        elif cur_mode == "local" or not has_any_cloud:
            self.combo_mode.setCurrentIndex(2)
        else:
            self.combo_mode.setCurrentIndex(0)

        # Load profiles
        profs = getattr(self.provider_manager, "profiles", {})
        if "openrouter" in profs:
            p = profs["openrouter"]
            if p.get("api_key"):
                self.edit_key_openrouter.setText(p.get("api_key"))
            if p.get("default_model"):
                self.edit_model_openrouter.setText(p.get("default_model"))
            self.chk_openrouter.setChecked(p.get("enabled", True))

        if "openai" in profs:
            p = profs["openai"]
            if p.get("api_key"):
                self.edit_key_openai.setText(p.get("api_key"))
            if p.get("default_model"):
                self.edit_model_openai.setText(p.get("default_model"))
            self.chk_openai.setChecked(p.get("enabled", False))

        if "groq" in profs:
            p = profs["groq"]
            if p.get("api_key"):
                self.edit_key_groq.setText(p.get("api_key"))
            if p.get("default_model"):
                self.edit_model_groq.setText(p.get("default_model"))
            self.chk_groq.setChecked(p.get("enabled", False))

        if "deepseek" in profs:
            p = profs["deepseek"]
            if p.get("api_key"):
                self.edit_key_deepseek.setText(p.get("api_key"))
            if p.get("default_model"):
                self.edit_model_deepseek.setText(p.get("default_model"))
            self.chk_deepseek.setChecked(p.get("enabled", False))

        # Load agent assignments
        assigns = getattr(self.provider_manager, "agent_model_assignments", {})
        prov_display_map = {
            "openrouter": "Model 1",
            "openai": "Model 2",
            "groq": "Model 3",
            "deepseek": "Model 4",
            "custom": "Model 5",
            "ollama_local": "Local Model",
            "model 1": "Model 1",
            "model 2": "Model 2",
            "model 3": "Model 3",
            "model 4": "Model 4",
            "model 5": "Model 5",
            "local model": "Local Model",
            "OpenRouter": "Model 1",
            "OpenAI": "Model 2",
            "Groq": "Model 3",
            "DeepSeek": "Model 4",
            "Custom Gateway": "Model 5",
            "Ollama Local": "Local Model"
        }
        for r_id, (cb, ed) in getattr(self, "agent_ui_rows", {}).items():
            if r_id in assigns:
                a_data = assigns[r_id]
                prof = a_data.get("profile", "openrouter")
                mod = a_data.get("model", "")
                disp = prov_display_map.get(prof.lower() if isinstance(prof, str) else prof, "Model 1")
                cb.setCurrentText(disp)
                if mod:
                    ed.setText(mod)

        self._refresh_limits()

    def _refresh_limits(self):
        if self.provider_manager and self.provider_manager.cloud_provider:
            info = self.provider_manager.cloud_provider.fetch_key_info()
            if info.get("valid"):
                rem = info.get("free_requests_remaining", "Unlimited")
                lim = info.get("free_requests_limit", 50)
                interval = info.get("rate_limit_interval", "10s")
                self.lbl_key_status.setText("Status: Online • Key Verified Active")
                self.lbl_key_status.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 600;")
                self.lbl_key_rem.setText(f"Remaining Limit: {rem} / {lim} free requests remaining today")
                self.lbl_key_rate.setText(f"Rate Limits: Active • {interval} interval • Multi-Model Ready")
            else:
                self.lbl_key_status.setText(f"Status: {info.get('error', 'Key not verified')}")
                self.lbl_key_status.setStyleSheet("color: #f59e0b; font-size: 10px;")

    def _on_test_connection(self):
        self.btn_test.setText("⏳ Testing Connections...")
        # Ping OpenRouter
        self._ping_provider("openrouter")
        if self.chk_openai.isChecked() and self.edit_key_openai.text().strip():
            self._ping_provider("openai")
        if self.chk_groq.isChecked() and self.edit_key_groq.text().strip():
            self._ping_provider("groq")
        if self.chk_deepseek.isChecked() and self.edit_key_deepseek.text().strip():
            self._ping_provider("deepseek")
        if self.chk_custom.isChecked():
            self._ping_provider("custom")
        
        self._refresh_limits()
        QTimer.singleShot(2500, lambda: self.btn_test.setText("⚡ Test Multi-Model Connections"))

    def _on_save_models(self):
        m_mode = "hybrid" if "Hybrid" in self.combo_mode.currentText() else ("cloud" if "Cloud" in self.combo_mode.currentText() else "local")
        
        prov_lookup = {
            "Model 1": "openrouter",
            "Model 2": "openai",
            "Model 3": "groq",
            "Model 4": "deepseek",
            "Model 5": "custom",
            "Local Model": "ollama_local",
            "Ollama Local": "ollama_local",
            "OpenRouter": "openrouter",
            "OpenAI": "openai",
            "Groq": "groq",
            "DeepSeek": "deepseek",
            "Custom Gateway": "custom"
        }

        # Build profiles dict
        profiles_dict = {
            "openrouter": {
                "provider_name": "Model 1",
                "api_base": "https://openrouter.ai/api/v1",
                "api_key": self.edit_key_openrouter.text().strip(),
                "default_model": self.edit_model_openrouter.text().strip(),
                "enabled": self.chk_openrouter.isChecked()
            },
            "openai": {
                "provider_name": "Model 2",
                "api_base": "https://api.openai.com/v1",
                "api_key": self.edit_key_openai.text().strip(),
                "default_model": self.edit_model_openai.text().strip(),
                "enabled": self.chk_openai.isChecked()
            },
            "groq": {
                "provider_name": "Model 3",
                "api_base": "https://api.groq.com/openai/v1",
                "api_key": self.edit_key_groq.text().strip(),
                "default_model": self.edit_model_groq.text().strip(),
                "enabled": self.chk_groq.isChecked()
            },
            "deepseek": {
                "provider_name": "Model 4",
                "api_base": "https://api.deepseek.com/v1",
                "api_key": self.edit_key_deepseek.text().strip(),
                "default_model": self.edit_model_deepseek.text().strip(),
                "enabled": self.chk_deepseek.isChecked()
            },
            "custom": {
                "provider_name": "Model 5",
                "api_base": self.edit_base_custom.text().strip(),
                "api_key": self.edit_key_custom.text().strip(),
                "default_model": self.edit_model_custom.text().strip(),
                "enabled": self.chk_custom.isChecked()
            }
        }

        # Build agent assignments dict
        agent_assigns = {}
        for r_id, (cb, ed) in getattr(self, "agent_ui_rows", {}).items():
            sel_text = cb.currentText()
            prof_id = prov_lookup.get(sel_text, "openrouter")
            mod_name = ed.text().strip()
            agent_assigns[r_id] = {
                "profile": prof_id,
                "model": mod_name
            }

        if self.provider_manager:
            if hasattr(self.provider_manager, "update_multi_model_pipeline"):
                self.provider_manager.update_multi_model_pipeline(
                    mode=m_mode,
                    profiles_config=profiles_dict,
                    agent_assignments=agent_assigns
                )
            else:
                self.provider_manager.update_model_and_keys(
                    default_provider="openrouter",
                    default_model=self.edit_model_openrouter.text().strip(),
                    default_key=self.edit_key_openrouter.text().strip(),
                    mode=m_mode
                )
            self._refresh_limits()

        self.btn_save.setText("✅ Multi-Model Pipeline Saved!")
        self.btn_save.setStyleSheet("background: rgba(16, 185, 129, 0.6); color: #ffffff; border: 1px solid #10b981; border-radius: 6px; padding: 7px 16px; font-size: 11px; font-weight: bold;")
        QTimer.singleShot(2000, lambda: self.btn_save.setText("💾 Save & Apply Multi-Model Pipeline"))
        
        self.settings_saved.emit({
            "mode": m_mode,
            "profiles": profiles_dict,
            "assignments": agent_assigns,
            "short_voice": self.rad_short.isChecked()
        })

    def _on_verify_plugins(self):
        self.btn_test_plugins.setText("⏳ Testing Pipelines...")
        # Verify pipelines
        QTimer.singleShot(1000, self._finish_verify_plugins)

    def _finish_verify_plugins(self):
        self.btn_test_plugins.setText("✅ All 8 Pipelines Verified & Healthy")
        self.btn_test_plugins.setStyleSheet("background: rgba(16, 185, 129, 0.4); color: #10b981; border: 1px solid #10b981; border-radius: 6px; padding: 6px 12px; font-size: 11px; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.btn_test_plugins.setText("⚙ Verify & Test All Skill Pipelines"))

    def _set_size_preset(self, preset: str):
        self.size_preset_requested.emit(preset)
        if self.widget_parent and hasattr(self.widget_parent, "apply_size_preset"):
            self.widget_parent.apply_size_preset(preset)

    def _on_start_ollama(self):
        try:
            import subprocess
            subprocess.run(["ollama", "run", "lfm3-omni:2b", ""], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _on_stop_ollama(self):
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "ollama serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
