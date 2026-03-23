"""
joint_panel.py  –  Per-joint column widget for Sync GUI
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QSlider, QGridLayout, QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


# Fields returned by get_currentStatus_parameters() in order
STATUS_FIELDS = [
    ("Torque Enable",     "Enable"),
    ("Current Id",        "current_Id"),
    ("Current Iq",        "current_Iq"),
    ("Velocity",          "current_velocity"),
    ("Position",          "current_position"),
    ("Temperature (°C)",  "Temprature_read"),
    ("SP Current",        "setpoint_current"),
    ("SP Velocity",       "setpoint_velocity"),
    ("SP Position",       "setpoint_position"),
]


class JointPanel(QFrame):
    """A single joint column widget."""

    enable_changed = pyqtSignal(int, bool)   # joint_id, enabled

    def __init__(self, joint_id: int, parent=None):
        super().__init__(parent)
        self.joint_id = joint_id
        self._value_labels: dict[str, QLabel] = {}
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        self.setObjectName("JointPanel")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        # ── Header ──────────────────────────────────────────────────────
        header = QLabel(f"Joint  {self.joint_id}")
        header.setObjectName("JointHeader")
        header.setAlignment(Qt.AlignCenter)
        root.addWidget(header)

        # ── Enable checkbox ─────────────────────────────────────────────
        self.enable_cb = QCheckBox("Enable")
        self.enable_cb.setObjectName("EnableCheck")
        self.enable_cb.stateChanged.connect(self._on_enable_changed)
        root.addWidget(self.enable_cb)

        # ── Separator ───────────────────────────────────────────────────
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setObjectName("Separator")
        root.addWidget(sep1)

        # ── Position setpoint ────────────────────────────────────────────
        sp_row = QVBoxLayout()
        sp_label = QLabel("Setpoint Position (°)")
        sp_label.setObjectName("SectionLabel")
        sp_row.addWidget(sp_label)

        slider_row = QHBoxLayout()
        self.pos_slider = QSlider(Qt.Horizontal)
        self.pos_slider.setRange(-180, 180)
        self.pos_slider.setValue(0)
        self.pos_slider.setTickInterval(45)
        self.pos_slider.setTickPosition(QSlider.TicksBelow)
        self.pos_slider.valueChanged.connect(self._on_slider_changed)

        self.pos_val_edit = QLineEdit("0")
        self.pos_val_edit.setObjectName("SliderValueEdit")
        self.pos_val_edit.setFixedWidth(52)
        self.pos_val_edit.setAlignment(Qt.AlignRight)
        self.pos_val_edit.setToolTip("Manuel giriş yapın ve Enter'a basın (-180 … 180)")
        self.pos_val_edit.editingFinished.connect(self._on_edit_finished)

        slider_row.addWidget(self.pos_slider)
        slider_row.addWidget(self.pos_val_edit)
        sp_row.addLayout(slider_row)

        # ── Current position readout (below slider) ──────────────────────
        cur_row = QHBoxLayout()
        cur_lbl = QLabel("Current Pos:")
        cur_lbl.setObjectName("ParamName")
        self.cur_pos_display = QLabel("—")
        self.cur_pos_display.setObjectName("CurPosValue")
        self.cur_pos_display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cur_row.addWidget(cur_lbl)
        cur_row.addWidget(self.cur_pos_display, stretch=1)
        sp_row.addLayout(cur_row)

        root.addLayout(sp_row)

        # ── Separator ───────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("Separator")
        root.addWidget(sep2)

        # ── Current box (Id / Iq / Total) ────────────────────────────────
        cur_sect_lbl = QLabel("Current")
        cur_sect_lbl.setObjectName("SectionLabel")
        root.addWidget(cur_sect_lbl)

        self.current_box = QFrame()
        self.current_box.setObjectName("CurrentBox")
        self.current_box.setFrameShape(QFrame.StyledPanel)
        cur_box_layout = QGridLayout(self.current_box)
        cur_box_layout.setContentsMargins(8, 6, 8, 6)
        cur_box_layout.setVerticalSpacing(3)
        cur_box_layout.setHorizontalSpacing(8)

        for row_i, (lbl_text, attr) in enumerate([
            ("Id:",    "_cur_id_lbl"),
            ("Iq:",    "_cur_iq_lbl"),
            ("Total:", "_cur_total_lbl"),
        ]):
            name_l = QLabel(lbl_text)
            name_l.setObjectName("ParamName")
            val_l  = QLabel("—")
            val_l.setObjectName("ParamValue")
            val_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cur_box_layout.addWidget(name_l, row_i, 0)
            cur_box_layout.addWidget(val_l,  row_i, 1)
            setattr(self, attr, val_l)

        root.addWidget(self.current_box)

        # ── Live parameters grid ─────────────────────────────────────────
        params_label = QLabel("Live Parameters")
        params_label.setObjectName("SectionLabel")
        root.addWidget(params_label)

        grid = QGridLayout()
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(8)
        for row, (display_name, key) in enumerate(STATUS_FIELDS):
            name_lbl = QLabel(display_name + ":")
            name_lbl.setObjectName("ParamName")
            val_lbl = QLabel("—")
            val_lbl.setObjectName("ParamValue")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(name_lbl, row, 0)
            grid.addWidget(val_lbl, row, 1)
            self._value_labels[key] = val_lbl

        root.addLayout(grid)
        root.addStretch()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def is_enabled(self) -> bool:
        return self.enable_cb.isChecked()

    def get_setpoint(self) -> float:
        return float(self.pos_slider.value())

    def update_params(self, data: list):
        """
        Update displayed values from get_currentStatus_parameters() result.
        data is a list of 9 values in STATUS_FIELDS order.
        """
        if not data or data[0] is None:
            return
        for i, (_, key) in enumerate(STATUS_FIELDS):
            if i >= len(data):
                break
            val = data[i]
            if val is None:
                text = "—"
            elif isinstance(val, float):
                text = f"{val:.3f}"
            elif isinstance(val, bool):
                text = "ON" if val else "OFF"
            elif isinstance(val, int) and key == "Enable":
                text = "ON" if val else "OFF"
            else:
                text = str(val)
            self._value_labels[key].setText(text)
            # Mirror current position below the slider
            if key == "current_position" and val is not None:
                self.cur_pos_display.setText(f"{val:.2f}°")

        # ── Update current box ────────────────────────────────────────────
        # STATUS_FIELDS indices: 1 = current_Id, 2 = current_Iq
        id_val  = data[1] if len(data) > 1 else None
        iq_val  = data[2] if len(data) > 2 else None
        self._update_current_box(id_val, iq_val)

    def clear_params(self):
        for lbl in self._value_labels.values():
            lbl.setText("—")
        self.cur_pos_display.setText("—")
        self._cur_id_lbl.setText("—")
        self._cur_iq_lbl.setText("—")
        self._cur_total_lbl.setText("—")
        self._set_current_box_alarm(False)

    CURRENT_ALARM_THRESHOLD = 2.0   # Ampere

    def _update_current_box(self, id_val, iq_val):
        """Refresh the Id/Iq/Total box and colour it red if over threshold."""
        def fmt(v):
            return f"{v:.3f} A" if v is not None else "—"

        self._cur_id_lbl.setText(fmt(id_val))
        self._cur_iq_lbl.setText(fmt(iq_val))

        if id_val is not None and iq_val is not None:
            total = abs(id_val) + abs(iq_val)
            self._cur_total_lbl.setText(f"{total:.3f} A")
            self._set_current_box_alarm(total > self.CURRENT_ALARM_THRESHOLD)
        else:
            self._cur_total_lbl.setText("—")
            self._set_current_box_alarm(False)

    def _set_current_box_alarm(self, alarm: bool):
        """Toggle red border/background on the current box."""
        self.current_box.setProperty("alarm", alarm)
        # Force stylesheet refresh
        self.current_box.style().unpolish(self.current_box)
        self.current_box.style().polish(self.current_box)

    # ------------------------------------------------------------------ #
    #  Slots
    # ------------------------------------------------------------------ #
    def _on_enable_changed(self, state):
        enabled = (state == Qt.Checked)
        self.enable_changed.emit(self.joint_id, enabled)
        if not enabled:
            self.clear_params()

    def _on_slider_changed(self, value):
        # Keep the edit box in sync when slider moves (don't cause a feedback loop)
        self.pos_val_edit.blockSignals(True)
        self.pos_val_edit.setText(str(value))
        self.pos_val_edit.blockSignals(False)

    def _on_edit_finished(self):
        text = self.pos_val_edit.text().strip().rstrip("°")
        try:
            value = int(round(float(text)))
            value = max(-180, min(180, value))   # clamp
            self.pos_slider.setValue(value)       # this triggers _on_slider_changed
        except ValueError:
            # Geçersiz giriş → eski değeri geri yaz
            self.pos_val_edit.setText(str(self.pos_slider.value()))
