"""
main.py  –  Sync GUI main window
Run from project root:  python sync_gui/main.py
"""

import sys
import os

# Ensure the library package is importable when run from any cwd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit,
    QFrame, QScrollArea, QSizePolicy,
    QStatusBar, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

import serial.tools.list_ports

from joint_panel import JointPanel
from comm_worker import CommWorker


# ── Stylesheet ───────────────────────────────────────────────────────────────
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #12131a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Top bar ── */
#TopBar {
    background-color: #1c1d27;
    border-bottom: 1px solid #2e2f3e;
    padding: 6px 12px;
}
#AppTitle {
    font-size: 17px;
    font-weight: bold;
    color: #a78bfa;
    letter-spacing: 1px;
}
#ConnectBtn {
    background-color: #7c3aed;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 18px;
    font-weight: bold;
}
#ConnectBtn:hover  { background-color: #6d28d9; }
#ConnectBtn:pressed{ background-color: #5b21b6; }

QComboBox, QLineEdit {
    background-color: #23243a;
    color: #e0e0e0;
    border: 1px solid #3a3b52;
    border-radius: 5px;
    padding: 4px 8px;
    min-width: 80px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #23243a;
    selection-background-color: #7c3aed;
    color: #e0e0e0;
}

/* ── Joint panels ── */
#JointPanel {
    background-color: #1c1d27;
    border: 1px solid #2e2f3e;
    border-radius: 10px;
    margin: 4px;
}
#JointHeader {
    font-size: 15px;
    font-weight: bold;
    color: #a78bfa;
    padding: 4px 0 2px 0;
}
#EnableCheck {
    font-size: 13px;
    color: #c4b5fd;
    spacing: 6px;
}
#EnableCheck::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 2px solid #6d28d9;
    background: #12131a;
}
#EnableCheck::indicator:checked {
    background: #7c3aed;
}
#SectionLabel {
    font-size: 11px;
    font-weight: bold;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
#ParamName  { color: #94a3b8; font-size: 12px; }
#ParamValue { color: #e2e8f0; font-size: 12px; font-weight: bold; }
#SliderValue {
    color: #a78bfa;
    font-size: 13px;
    font-weight: bold;
}
#SliderValueEdit {
    background-color: #23243a;
    color: #a78bfa;
    border: 1px solid #6d28d9;
    border-radius: 5px;
    padding: 2px 4px;
    font-size: 13px;
    font-weight: bold;
}
#SliderValueEdit:focus { border-color: #a78bfa; }
#CurPosValue {
    color: #34d399;
    font-size: 13px;
    font-weight: bold;
}
#Separator {
    color: #2e2f3e;
    max-height: 1px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #2e2f3e;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7c3aed;
    width: 14px; height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background: #6d28d9;
    border-radius: 3px;
}

/* ── Current box ── */
#CurrentBox {
    background-color: #161722;
    border: 1px solid #2e2f3e;
    border-radius: 7px;
}
#CurrentBox[alarm="true"] {
    background-color: #2d0e0e;
    border: 2px solid #dc2626;
}

/* ── Action bar ── */
#ActionBar {
    background-color: #1c1d27;
    border-top: 1px solid #2e2f3e;
    padding: 8px 16px;
}
#SyncDriveBtn {
    background-color: #059669;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 32px;
    font-size: 14px;
    font-weight: bold;
    min-width: 160px;
}
#SyncDriveBtn:hover  { background-color: #047857; }
#SyncDriveBtn:pressed{ background-color: #065f46; }
#SyncDriveBtn:disabled { background-color: #374151; color: #6b7280; }

#TorqueBtn {
    background-color: #1e40af;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 24px;
    font-size: 14px;
    font-weight: bold;
    min-width: 180px;
}
#TorqueBtn:hover   { background-color: #1d4ed8; }
#TorqueBtn:pressed { background-color: #1e3a8a; }
#TorqueBtn:checked {
    background-color: #dc2626;
}
#TorqueBtn:checked:hover  { background-color: #b91c1c; }
#TorqueBtn:disabled { background-color: #374151; color: #6b7280; }

/* ── Status / notification bar ── */
#StatusBar {
    background-color: #0f1117;
    border-top: 1px solid #1e2030;
    padding: 3px 12px;
    min-height: 24px;
}
#StatusLabel {
    color: #64748b;
    font-size: 11px;
}
#TimeoutLabel {
    color: #f97316;
    font-size: 11px;
    font-weight: bold;
}
"""


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acrome Joint – Sync GUI")
        self.setMinimumSize(960, 700)
        self.resize(1200, 780)

        # Timeout counters per joint
        self._timeout_counts = [0, 0, 0, 0]

        # Worker thread
        self._worker = CommWorker()
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.timeout_event.connect(self._on_timeout)
        self._worker.connection_status.connect(self._on_conn_status)
        self._worker.start()

        self._connected = False
        self._build_ui()
        self._update_action_buttons()
        self._refresh_ports()

    # ------------------------------------------------------------------ #
    #  UI building
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        root_layout.addWidget(self._build_top_bar())
        root_layout.addWidget(self._build_columns_area(), stretch=1)
        root_layout.addWidget(self._build_action_bar())
        root_layout.addWidget(self._build_status_strip())

    # ── Top bar ─────────────────────────────────────────────────────────
    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        title = QLabel("⚙  Acrome Sync GUI")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding))

        lbl_port = QLabel("Port:")
        lbl_port.setStyleSheet("color:#94a3b8;")
        layout.addWidget(lbl_port)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(130)
        layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setStyleSheet(
            "QPushButton{background:#23243a;border:1px solid #3a3b52;"
            "border-radius:5px;color:#a78bfa;font-size:14px;}"
            "QPushButton:hover{background:#2e2f3e;}"
        )
        refresh_btn.setToolTip("Refresh port list")
        refresh_btn.clicked.connect(self._refresh_ports)
        layout.addWidget(refresh_btn)

        lbl_baud = QLabel("Baud:")
        lbl_baud.setStyleSheet("color:#94a3b8;")
        layout.addWidget(lbl_baud)

        self.baud_edit = QComboBox()
        self.baud_edit.addItems(["921600", "115200", "57600", "38400", "19200"])
        self.baud_edit.setEditable(True)
        self.baud_edit.setMinimumWidth(90)
        layout.addWidget(self.baud_edit)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("ConnectBtn")
        self.connect_btn.clicked.connect(self._on_connect_toggle)
        layout.addWidget(self.connect_btn)

        return bar

    # ── 4-column joint area ──────────────────────────────────────────────
    def _build_columns_area(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea{border:none;background:#12131a;}")

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setSpacing(8)
        h_layout.setContentsMargins(12, 12, 12, 12)

        self.panels: list[JointPanel] = []
        for i in range(4):
            panel = JointPanel(i)
            panel.enable_changed.connect(self._on_enable_changed)
            h_layout.addWidget(panel, stretch=1)
            self.panels.append(panel)

        scroll.setWidget(container)
        return scroll

    # ── Action bar ───────────────────────────────────────────────────────
    def _build_action_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("ActionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        lbl = QLabel("Global Controls")
        lbl.setStyleSheet("color:#64748b; font-size:11px; font-weight:bold;")
        layout.addWidget(lbl)
        layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding))

        self.torque_btn = QPushButton("Torque Enable: OFF")
        self.torque_btn.setObjectName("TorqueBtn")
        self.torque_btn.setCheckable(True)
        self.torque_btn.toggled.connect(self._on_torque_toggle)
        layout.addWidget(self.torque_btn)

        self.sync_btn = QPushButton("⚡  Sync Drive")
        self.sync_btn.setObjectName("SyncDriveBtn")
        self.sync_btn.clicked.connect(self._on_sync_drive)
        layout.addWidget(self.sync_btn)

        return bar

    # ── Status strip ─────────────────────────────────────────────────────
    def _build_status_strip(self) -> QWidget:
        strip = QWidget()
        strip.setObjectName("StatusBar")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(20)

        self.conn_label = QLabel("● Not connected")
        self.conn_label.setObjectName("StatusLabel")
        layout.addWidget(self.conn_label)

        layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding))

        lbl_t = QLabel("Timeouts:")
        lbl_t.setObjectName("StatusLabel")
        layout.addWidget(lbl_t)

        self.timeout_labels: list[QLabel] = []
        for i in range(4):
            lbl = QLabel(f"J{i}: 0")
            lbl.setObjectName("StatusLabel")
            layout.addWidget(lbl)
            self.timeout_labels.append(lbl)

        return strip

    # ------------------------------------------------------------------ #
    #  Port management
    # ------------------------------------------------------------------ #
    def _refresh_ports(self):
        self.port_combo.clear()
        ports = list(serial.tools.list_ports.comports())
        if ports:
            for p, desc, _ in sorted(ports):
                self.port_combo.addItem(f"{p} – {desc}", userData=p)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("(no ports found)", userData="")

    def _on_connect_toggle(self):
        if not self._connected:
            port_name = self.port_combo.currentData() or self.port_combo.currentText().split("–")[0].strip()
            if not port_name:
                self.conn_label.setText("● No port selected")
                return
            try:
                baudrate = int(self.baud_edit.currentText())
            except ValueError:
                baudrate = 921600
            self._worker.connect_port(port_name, baudrate)
        else:
            self._worker.disconnect_port()

    # ------------------------------------------------------------------ #
    #  Worker signal handlers
    # ------------------------------------------------------------------ #
    @pyqtSlot(bool, str)
    def _on_conn_status(self, connected: bool, message: str):
        self._connected = connected
        dot = "●"
        color = "#10b981" if connected else "#ef4444"
        self.conn_label.setText(f'<span style="color:{color}">{dot}</span> {message}')
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self._update_action_buttons()

    @pyqtSlot(int, list)
    def _on_data_ready(self, joint_id: int, data: list):
        self.panels[joint_id].update_params(data)

    @pyqtSlot(int)
    def _on_timeout(self, joint_id: int):
        self._timeout_counts[joint_id] += 1
        lbl = self.timeout_labels[joint_id]
        n = self._timeout_counts[joint_id]
        lbl.setObjectName("TimeoutLabel" if n > 0 else "StatusLabel")
        lbl.setText(f"J{joint_id}: {n}")
        lbl.setStyleSheet("color: #f97316;" if n > 0 else "")

    # ------------------------------------------------------------------ #
    #  GUI event handlers
    # ------------------------------------------------------------------ #
    def _on_enable_changed(self, joint_id: int, enabled: bool):
        flags = [p.is_enabled() for p in self.panels]
        self._worker.update_joint_enables(flags)
        self._update_action_buttons()

    def _on_sync_drive(self):
        setpoints = {}
        for i, panel in enumerate(self.panels):
            if panel.is_enabled():
                setpoints[i] = panel.get_setpoint()
        if setpoints:
            self._worker.send_sync_drive(setpoints)

    def _on_torque_toggle(self, checked: bool):
        self.torque_btn.setText(f"Torque Enable: {'ON' if checked else 'OFF'}")
        flags = [p.is_enabled() for p in self.panels]
        self._worker.send_torque_enable(checked, flags)

    def _update_action_buttons(self):
        any_enabled = any(p.is_enabled() for p in self.panels)
        ok = self._connected and any_enabled
        self.sync_btn.setEnabled(ok)
        self.torque_btn.setEnabled(ok)

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #
    def closeEvent(self, event):
        self._worker.stop()
        self._worker.disconnect_port()
        self._worker.quit()
        self._worker.wait(2000)
        super().closeEvent(event)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Try to set a nice font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
