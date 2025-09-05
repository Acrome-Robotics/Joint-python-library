# app.py
# pip install PySide6 pyqtgraph numpy

from PySide6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
import time
from typing import Optional
from gui.joint_device import *
from gui.ramp_trajectory import *   # <-- S-Curve Ramp sınıfını kullanacağız
from gui.limits import *

NUM_FMT = "{:.3f}"  # tabloda göstereceğimiz sayısal format


# =========================
#  OPERATION için parametre grupları
# =========================
OP_PARAM_GROUPS = {
    1: [  # Plot 1 yanındaki tablo (8 adet)
        "current_Id",
        "current_Iq",
        "currentId_loop_kp",
        "currentId_loop_ki",
        "currentId_loop_kd",
        "currentIq_loop_kp",
        "currentIq_loop_ki",
        "currentIq_loop_kd",
    ],
    2: [  # Plot 2 yanındaki tablo (4 adet)
        "current_velocity",
        "velocity_loop_kp",
        "velocity_loop_ki",
        "velocity_loop_kd",
    ],
    3: [  # Plot 3 yanındaki tablo (4 adet)
        "current_position",
        "position_loop_kp",
        "position_loop_ki",
        "position_loop_kd",
    ],
}


# =========================
#  Ortak Signal Bus
# =========================
class SignalBus(QtCore.QObject):
    tabChanged = QtCore.Signal(int, str)
    configParamChanged = QtCore.Signal(str, str)
    operationParamChanged = QtCore.Signal(int, str, str)
    refreshClicked = QtCore.Signal()
    restartClicked = QtCore.Signal()
    configSaveClicked = QtCore.Signal()
    FactoryResetClicked = QtCore.Signal()
    newTimedData = QtCore.Signal(float, float, float, float, float, float, float, float)  # y1,y2,y3,y4, s1,s2,s3, t
    idChanged = QtCore.Signal(str)            # Uygulama kimliği değiştiğinde yayınlanır
    enableToggled = QtCore.Signal(bool)       # ON/OFF değişimi için
    enableStateUpdated = QtCore.Signal(bool)  # cihazdan gelen enable -> UI

    # --- S-Curve eklentisi için yeni sinyaller ---
    sCurveToggled = QtCore.Signal(bool)                   # S-Curve enable/disable
    sCurvePlanRequested = QtCore.Signal(float, float, float, float)  # target, vmax, a_des, t_des


# =========================
#  Başlangıç ID Diyaloğu
# =========================
class StartupDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cihaz ID Girişi")
        self.setModal(True)
        self.id_value: Optional[str] = None

        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.leID = QtWidgets.QLineEdit()
        self.leID.setPlaceholderText("Örn: 42")
        form.addRow("ID:", self.leID)

        self.cbRemember = QtWidgets.QCheckBox("Bu ID'yi hatırla")
        layout.addLayout(form)
        layout.addWidget(self.cbRemember)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # QSettings: Son ID’yi yükle
        sett = QtCore.QSettings("Acrome", "UartUiApp")
        last_id = sett.value("last_id", "", type=str)
        if last_id:
            self.leID.setText(last_id)
            self.cbRemember.setChecked(True)

    def _on_ok(self):
        text = self.leID.text().strip()
        if not text:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen bir ID girin.")
            return
        self.id_value = text
        # Hatırlama
        sett = QtCore.QSettings("Acrome", "UartUiApp")
        if self.cbRemember.isChecked():
            sett.setValue("last_id", text)
        else:
            sett.remove("last_id")
        self.accept()


# =========================
#  CONFIG Sekmesi
# =========================
class ConfigTab(QtWidgets.QWidget):
    def __init__(self, bus: SignalBus, parent=None):
        super().__init__(parent)
        self.bus = bus
        self._suppress_cell_signal = False

        layout = QtWidgets.QHBoxLayout(self)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

        self.parameters = [
            {"name": 'Header', "value": "", "read_only": True},
            {"name": 'DeviceID', "value": "", "read_only": True},
            {"name": 'DeviceFamily', "value": "", "read_only": True},
            {"name": 'PackageSize', "value": "", "read_only": True},
            {"name": 'Command', "value": "", "read_only": True},
            {"name": 'Status', "value": "", "read_only": True},
            {"name": 'HardwareVersion', "value": "", "read_only": True},
            {"name": 'SoftwareVersion', "value": "", "read_only": True},
            {"name": 'Baudrate', "value": "", "read_only": True},
            {"name": 'OperationMode', "value": "", "read_only": False},
            {"name": 'Enable', "value": "", "read_only": False},
            {"name": 'Vbus_read', "value": "", "read_only": True},
            {"name": 'Temprature_read', "value": "", "read_only": True},
            {"name": 'currentId_loop_kp', "value": "", "read_only": False},
            {"name": 'currentId_loop_ki', "value": "", "read_only": False},
            {"name": 'currentId_loop_kd', "value": "", "read_only": False},
            {"name": 'currentIq_loop_kp', "value": "", "read_only": False},
            {"name": 'currentIq_loop_ki', "value": "", "read_only": False},
            {"name": 'currentIq_loop_kd', "value": "", "read_only": False},
            {"name": 'velocity_loop_kp', "value": "", "read_only": False},
            {"name": 'velocity_loop_ki', "value": "", "read_only": False},
            {"name": 'velocity_loop_kd', "value": "", "read_only": False},
            {"name": 'position_loop_kp', "value": "", "read_only": False},
            {"name": 'position_loop_ki', "value": "", "read_only": False},
            {"name": 'position_loop_kd', "value": "", "read_only": False},
            {"name": 'max_position', "value": "", "read_only": False},
            {"name": 'min_position', "value": "", "read_only": False},
            {"name": 'max_velocity', "value": "", "read_only": False},
            {"name": 'max_current', "value": "", "read_only": False},
            {"name": 'current_Va', "value": "", "read_only": True},
            {"name": 'current_Vb', "value": "", "read_only": True},
            {"name": 'current_Vc', "value": "", "read_only": True},
            {"name": 'current_Ia', "value": "", "read_only": True},
            {"name": 'current_Ib', "value": "", "read_only": True},
            {"name": 'current_Ic', "value": "", "read_only": True},
            {"name": 'current_Id', "value": "", "read_only": True},
            {"name": 'current_Iq', "value": "", "read_only": True},
            {"name": 'current_velocity', "value": "", "read_only": True},
            {"name": 'current_position', "value": "", "read_only": True},
            {"name": 'current_electrical_degree', "value": "", "read_only": True},
            {"name": 'current_electrical_radian', "value": "", "read_only": True},
            {"name": 'setpoint_current', "value": "", "read_only": False},
            {"name": 'setpoint_velocity', "value": "", "read_only": False},
            {"name": 'setpoint_position', "value": "", "read_only": False},
            {"name": 'openloop_voltage_size', "value": "", "read_only": False},
            {"name": 'openloop_angle_degree', "value": "", "read_only": False},
            {"name": 'current_lock_angle_degree', "value": "", "read_only": False},
            {"name": 'Config_TimeStamp', "value": "", "read_only": False},
            {"name": 'Config_Description', "value": "", "read_only": False},
            {"name": 'CRCValue', "value": "", "read_only": True},
        ]

        # İlk değerleri cihazdan çek
        for var in self.parameters:
            var["value"] = Device.get_variables(Index_Joint[var["name"]])[0]

        self._populate_table()
        self.table.cellChanged.connect(self._on_cell_changed)

        # Sağ buton sütunu
        btn_col = QtWidgets.QVBoxLayout()
        self.btnRefresh = QtWidgets.QPushButton("Refresh")
        self.btnRestart = QtWidgets.QPushButton("Restart")
        self.btnConfigSave = QtWidgets.QPushButton("Config Save")
        self.btnApply = QtWidgets.QPushButton("Apply")
        for b in (self.btnRefresh, self.btnRestart, self.btnConfigSave, self.btnApply):
            b.setMinimumHeight(40)
            btn_col.addWidget(b)
        btn_col.addStretch()

        self.btnRefresh.clicked.connect(self.bus.refreshClicked)
        self.btnRestart.clicked.connect(self.bus.restartClicked)
        self.btnConfigSave.clicked.connect(self.bus.configSaveClicked)
        self.btnApply.clicked.connect(self.bus.FactoryResetClicked)

        layout.addWidget(self.table, 3)
        layout.addLayout(btn_col, 1)

        print("config tab init")

    def _populate_table(self):
        self._suppress_cell_signal = True
        self.table.setRowCount(len(self.parameters))
        for row, p in enumerate(self.parameters):
            name_item = QtWidgets.QTableWidgetItem(p["name"])
            name_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.table.setItem(row, 0, name_item)

            val_item = QtWidgets.QTableWidgetItem(str(p["value"]))
            if p["read_only"]:
                val_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.table.setItem(row, 1, val_item)
        self._suppress_cell_signal = False

    def _on_cell_changed(self, row, column):
        if self._suppress_cell_signal or column != 1:
            return
        name = self.table.item(row, 0).text()
        value = self.table.item(row, 1).text()
        if self.parameters[row]["read_only"]:
            self._suppress_cell_signal = True
            self.table.item(row, 1).setText(str(self.parameters[row]["value"]))
            self._suppress_cell_signal = False
            return
        self.parameters[row]["value"] = value
        self.bus.configParamChanged.emit(name, value)

    def refresh_from_device(self, new_params: dict):
        # Şu an parametreleri zaten self.parameters'tan alıyoruz
        self._populate_table()


# =========================
#  OPERATION Sekmesi
# =========================
class OperationPanel(QtWidgets.QGroupBox):
    def __init__(self, bus: SignalBus, panel_id: int, title: str, plot_mode: str = "single",
                 extra_param_label: str | None = None, extra_param_key: str | None = None, parent=None):
        super().__init__(title, parent)
        self.bus = bus
        self.panel_id = panel_id
        self.plot_mode = plot_mode
        self._suppress_cell_signal = False

        # --- ekstra parametre meta ---
        self.extra_param_label = extra_param_label  # UI'da gösterilecek isim (ör. current_setpoint)
        self.extra_param_key = extra_param_key      # Index_Joint anahtarı (ör. setpoint_current)

        layout = QtWidgets.QHBoxLayout(self)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel('bottom', 'Time', units='s')
        self.plot.setLabel('left', 'Value', units='')

        self.curve1 = self.plot.plot(pen=pg.mkPen(width=2))
        self.curve2 = None
        if self.plot_mode == "dual":
            self.curve2 = self.plot.plot(pen=pg.mkPen(color='c', width=2))

        # --- setpoint curve (yellow)
        self.curve_sp = self.plot.plot(pen=pg.mkPen('y', width=2))

        self.max_points = 1000
        self.tbuf, self.y1buf, self.y2buf, self.spbuf = [], [], [], []

        # Sağ kolon: tablo + alt setpoint alanı + (panel3 için S-Curve kutusu eklenecek)
        self.right_col = QtWidgets.QVBoxLayout()

        # Parametre tablosu (scrollable)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setRowCount(10)
        for i in range(10):
            name_item = QtWidgets.QTableWidgetItem(f"P{i+1}")
            name_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.table.setItem(i, 0, name_item)
            value_item = QtWidgets.QTableWidgetItem("0")
            self.table.setItem(i, 1, value_item)
        self.table.cellChanged.connect(self._on_cell_changed)

        self.right_col.addWidget(self.table, 1)

        # Alt sabit setpoint alanı (tablodan ayrı ve sabit)
        if self.extra_param_label and self.extra_param_key:
            self.extraBox = QtWidgets.QGroupBox("Setpoint")
            form = QtWidgets.QHBoxLayout(self.extraBox)
            self.lblExtra = QtWidgets.QLabel(self.extra_param_label)
            self.leExtra = QtWidgets.QLineEdit()
            self.btnExtraSet = QtWidgets.QPushButton("Set")
            self.leExtra.setPlaceholderText("value")
            form.addWidget(self.lblExtra)
            form.addWidget(self.leExtra, 1)
            form.addWidget(self.btnExtraSet)
            self.right_col.addWidget(self.extraBox, 0)

            # Enter veya buton ile SET
            self.leExtra.returnPressed.connect(self._emit_extra_set)
            self.btnExtraSet.clicked.connect(self._emit_extra_set)
        else:
            self.extraBox = None
            self.lblExtra = None
            self.leExtra = None
            self.btnExtraSet = None

        layout.addWidget(self.plot, 3)
        layout.addLayout(self.right_col, 2)

    # ---- alt setpoint alanını programatik güncellemek için (şu an otomatik yazmıyoruz)
    def set_extra_param_value(self, text: str):
        if self.leExtra is not None:
            self.leExtra.setText(str(text))

    def set_extra_enabled(self, enabled: bool):
        """Setpoint giriş kutusu ve butonunu aç/kapat."""
        if self.leExtra is not None:
            self.leExtra.setEnabled(enabled)
        if self.btnExtraSet is not None:
            self.btnExtraSet.setEnabled(enabled)

    def add_widget_to_side(self, w: QtWidgets.QWidget):
        """Sağ kolona harici bir widget eklemek için yardımcı."""
        self.right_col.addWidget(w, 0)

    def _emit_extra_set(self):
        if self.extra_param_key and self.leExtra:
            value = self.leExtra.text()
            # Panel kimliği ve INDEX anahtar adı ile yayınla
            self.bus.operationParamChanged.emit(self.panel_id, self.extra_param_key, value)

    # ---- OPERATION panel yardımcıları ----
    def set_param_names(self, names: list[str]):
        """Sağdaki tabloya verilen isimleri yazar; kalan satırlara P# bırakır."""
        self._suppress_cell_signal = True
        for i in range(10):
            nm = names[i] if i < len(names) else f"P{i+1}"
            self.table.item(i, 0).setText(str(nm))
        self._suppress_cell_signal = False

    def set_read_only(self, readonly_names: set[str]):
        """Value hücresini verilen isimler için salt-okunur yapar."""
        self._suppress_cell_signal = True
        for r in range(self.table.rowCount()):
            nm = self.table.item(r, 0).text()
            val_item = self.table.item(r, 1)
            if nm in readonly_names:
                val_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            else:
                val_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        self._suppress_cell_signal = False

    def _on_cell_changed(self, row, column):
        if self._suppress_cell_signal or column != 1:
            return
        name = self.table.item(row, 0).text()
        value = self.table.item(row, 1).text()
        self.bus.operationParamChanged.emit(self.panel_id, name, value)

    def push_data(self, t: float, y1: float, y2: Optional[float] = None, sp: Optional[float] = None):
        self.tbuf.append(t)
        self.y1buf.append(y1)
        if self.curve2 is not None:
            self.y2buf.append(y2 if (y2 is not None) else 0.0)
        self.spbuf.append(sp if (sp is not None) else 0.0)

        if len(self.tbuf) > self.max_points:
            self.tbuf = self.tbuf[-self.max_points:]
            self.y1buf = self.y1buf[-self.max_points:]
            if self.curve2 is not None:
                self.y2buf = self.y2buf[-self.max_points:]
            self.spbuf = self.spbuf[-self.max_points:]

        self.curve1.setData(self.tbuf, self.y1buf)
        if self.curve2 is not None:
            self.curve2.setData(self.tbuf, self.y2buf)
        self.curve_sp.setData(self.tbuf, self.spbuf)

    def set_params_bulk(self, mapping: dict):
        name_to_row = {self.table.item(r, 0).text(): r for r in range(self.table.rowCount())}
        self._suppress_cell_signal = True
        for name, val in mapping.items():
            if name in name_to_row:
                r = name_to_row[name]
                self.table.item(r, 1).setText(str(val))
        self._suppress_cell_signal = False


class OperationTab(QtWidgets.QWidget):
    def __init__(self, bus: SignalBus, parent=None):
        super().__init__(parent)
        self.bus = bus
        self._suppress_enable_signal = False  # UI güncellerken sinyali bastırmak için
        self.bus.enableStateUpdated.connect(self.set_enable_ui)

        layout = QtWidgets.QVBoxLayout(self)

        # ---- Üst bar: Enable switch
        topbar = QtWidgets.QHBoxLayout()
        topbar.addStretch()
        self.enableSwitch = QtWidgets.QCheckBox("Enable")
        self.enableSwitch.setTristate(False)
        # (İsteğe bağlı) switch görünümü için basit bir stil:
        self.enableSwitch.setStyleSheet("""
            QCheckBox::indicator { width: 46px; height: 26px; }
            QCheckBox::indicator:unchecked { image: none; border-radius: 13px; background: #bbb; }
            QCheckBox::indicator:unchecked:hover { background: #aaa; }
            QCheckBox::indicator:checked { image: none; border-radius: 13px; background: #4caf50; }
            QCheckBox { padding: 4px; }
        """)
        self.enableSwitch.toggled.connect(self._on_enable_toggled)
        topbar.addWidget(self.enableSwitch)
        layout.addLayout(topbar)

        # ---- Paneller
        self.panel1 = OperationPanel(
            bus, panel_id=1, title="Plot 1 (Two Traces)", plot_mode="dual",
            extra_param_label="current_setpoint", extra_param_key="setpoint_current"
        )
        self.panel2 = OperationPanel(
            bus, panel_id=2, title="Plot 2 (Single Trace)", plot_mode="single",
            extra_param_label="velocity_setpoint", extra_param_key="setpoint_velocity"
        )
        self.panel3 = OperationPanel(
            bus, panel_id=3, title="Plot 3 (Single Trace)", plot_mode="single",
            extra_param_label="position_setpoint", extra_param_key="setpoint_position"
        )
        layout.addWidget(self.panel1)
        layout.addWidget(self.panel2)
        layout.addWidget(self.panel3)

        # İsimleri yaz
        self.panel1.set_param_names(OP_PARAM_GROUPS[1])
        self.panel2.set_param_names(OP_PARAM_GROUPS[2])
        self.panel3.set_param_names(OP_PARAM_GROUPS[3])

        # --- Panel 3 (Position) için S-Curve Planner UI'sı ---
        self._build_scurve_ui(self.panel3)

        # Cihazdan veri akışı
        self.bus.newTimedData.connect(self._on_new_timed_data)

        print("operation tab init")

    # S-Curve planner kutusu
    def _build_scurve_ui(self, position_panel: OperationPanel):
        gb = QtWidgets.QGroupBox("S-Curve Planner")
        vbox = QtWidgets.QVBoxLayout(gb)

        # Enable checkbox
        self.cbSCurve = QtWidgets.QCheckBox("Enable S-Curve")
        vbox.addWidget(self.cbSCurve)

        # Form inputs
        form = QtWidgets.QFormLayout()
        self.leTarget = QtWidgets.QLineEdit()
        self.leVmax = QtWidgets.QLineEdit()
        self.leAmax = QtWidgets.QLineEdit()
        self.leTdes = QtWidgets.QLineEdit()

        self.leTarget.setPlaceholderText("target_position")
        self.leVmax.setPlaceholderText("max_velocity")
        self.leAmax.setPlaceholderText("desired_acceleration")
        self.leTdes.setPlaceholderText("desired_time")

        form.addRow("Target Position:", self.leTarget)
        form.addRow("Max Velocity:", self.leVmax)
        form.addRow("Desired Accel.:", self.leAmax)
        form.addRow("Desired Time:", self.leTdes)
        vbox.addLayout(form)

        # Buttons
        hbtn = QtWidgets.QHBoxLayout()
        self.btnPlan = QtWidgets.QPushButton("Plan")
        self.btnPlan.setToolTip("Plan now (x0 = current_position)")
        hbtn.addStretch()
        hbtn.addWidget(self.btnPlan)
        vbox.addLayout(hbtn)

        # Add to panel 3 right side
        position_panel.add_widget_to_side(gb)

        # Connections
        self.cbSCurve.toggled.connect(self._on_scurve_toggled_ui)
        self.btnPlan.clicked.connect(self._emit_plan_from_ui)
        self.leTarget.returnPressed.connect(self._emit_plan_from_ui)  # target girilince anında planla

    def _on_scurve_toggled_ui(self, checked: bool):
        # UI etkisi: S-Curve açıldığında manuel position_setpoint girişini kapat
        self.bus.sCurveToggled.emit(checked)

    def _emit_plan_from_ui(self):
        def _as_float(le: QtWidgets.QLineEdit, default: float = 0.0) -> float:
            try:
                return float(le.text())
            except Exception:
                return default

        target = _as_float(self.leTarget, 0.0)
        vmax = _as_float(self.leVmax, 0.0)
        a_des = _as_float(self.leAmax, 0.0)
        t_des = _as_float(self.leTdes, 0.0)
        self.bus.sCurvePlanRequested.emit(target, vmax, a_des, t_des)

    def _on_new_timed_data(self, y1, y2, y3, y4, s1, s2, s3, t):
        # Plot lines + yellow setpoints
        self.panel1.push_data(t, y1, y2, s1)   # Id, Iq, setpoint_current
        self.panel2.push_data(t, y3, sp=s2)    # current_velocity, setpoint_velocity
        self.panel3.push_data(t, y4, sp=s3)    # current_position, setpoint_position

        # Keep the small tables synced with live values
        self.panel1.set_params_bulk({
            "current_Id": NUM_FMT.format(y1),
            "current_Iq": NUM_FMT.format(y2),
        })
        self.panel2.set_params_bulk({
            "current_velocity": NUM_FMT.format(y3),
        })
        self.panel3.set_params_bulk({
            "current_position": NUM_FMT.format(y4),
        })

    def reload_from_device(self):
        """Panel isimlerine göre Device'tan değer çek ve tabloları doldur."""
        def pull(names: list[str]) -> dict:
            out = {}
            for nm in names:
                if not nm or nm.startswith("P"):
                    continue
                try:
                    idx = Index_Joint[nm]
                    out[nm] = Device.get_variables(idx)[0]
                except Exception:
                    out[nm] = ""
            return out

        m1 = pull(OP_PARAM_GROUPS[1])
        m2 = pull(OP_PARAM_GROUPS[2])
        m3 = pull(OP_PARAM_GROUPS[3])

        self.panel1.set_params_bulk(m1)
        self.panel2.set_params_bulk(m2)
        self.panel3.set_params_bulk(m3)

    def _on_enable_toggled(self, checked: bool):
        if self._suppress_enable_signal:
            return
        # Switch değişince bus üzerinden ana pencereye bildir
        self.bus.enableToggled.emit(checked)

    def set_enable_ui(self, checked: bool):
        """Cihazdan okunan enable durumunu UI’a yaz (sinyal üretmeden)."""
        self._suppress_enable_signal = True
        try:
            self.enableSwitch.setChecked(bool(checked))
        finally:
            self._suppress_enable_signal = False


# =========================
#  Ana Pencere
# =========================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, device_id: str):
        super().__init__()
        self.setWindowTitle("ACROME JOINT BLDC DRIVER GUI")
        self.bus = SignalBus()
        self.current_id = device_id  # Girilen ID
        self.bus.idChanged.emit(self.current_id)

        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        self.configTab = ConfigTab(self.bus)
        self.operationTab = OperationTab(self.bus)
        self.tabs.addTab(self.configTab, "CONFIG")
        self.tabs.addTab(self.operationTab, "OPERATION")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._connect_bus_handlers()

        self.resize(1200, 900)

        self._op_timer = QtCore.QTimer(self)
        self._op_timer.timeout.connect(self._operation_tick)
        self._op_t0 = None  # OPERATION sekmesine girildiği anın referansı

        # ---- Read-only bilgisini CONFIG'ten al ve OPERATION tablolara uygula
        ro_names = {p["name"] for p in self.configTab.parameters if p.get("read_only", False)}
        self.operationTab.panel1.set_read_only(ro_names)
        self.operationTab.panel2.set_read_only(ro_names)
        self.operationTab.panel3.set_read_only(ro_names)

        # ---- S-Curve çalışma durumları ----
        self._s_curve_enabled: bool = False
        self._ramp: Optional[Ramp] = None
        self._last_current_position: float = 0.0  # her tick'te güncellenir

        print("main window init")

    # ------- Hook Bağlantıları -------
    def _connect_bus_handlers(self):
        self.bus.tabChanged.connect(self._on_tab_hook)
        self.bus.configParamChanged.connect(self._on_config_param_set)
        self.bus.operationParamChanged.connect(self._on_operation_param_set)
        self.bus.refreshClicked.connect(self._on_refresh_clicked)
        self.bus.restartClicked.connect(self._on_restart_clicked)
        self.bus.configSaveClicked.connect(self._on_config_save_clicked)
        self.bus.FactoryResetClicked.connect(self._on_config_reset_clicked)
        self.bus.enableToggled.connect(self._on_enable_toggled)

        # S-Curve sinyalleri
        self.bus.sCurveToggled.connect(self._on_scurve_toggled)
        self.bus.sCurvePlanRequested.connect(self._on_scurve_plan_requested)

    # ------- Tab Geçiş Kancası -------
    def _on_tab_changed(self, index: int):
        name = self.tabs.tabText(index)
        self.bus.tabChanged.emit(index, name)

        if name == "OPERATION":
            # OPERATION'a girildi: zaman referansı ve periyodik GET
            self._op_t0 = time.perf_counter()
            self._op_timer.start(30)   # ~33 Hz
        else:
            # OPERATION’dan çıkıldı: durdur
            self._op_timer.stop()

    def _operation_tick(self):
        """
        Periyodik GET: Device'tan değerleri çek ve zaman damgası ile yayınla.
        Ayrıca S-Curve açıksa her tick'te step() çağırıp position setpoint yollar.
        """
        parameters = Device.get_FOC_parameters(3)
        t_abs = time.perf_counter()
        t_rel = t_abs - (self._op_t0 or t_abs)

        y1 = parameters[1]
        y2 = parameters[2]
        y3 = parameters[3]
        y4 = parameters[4]
        self._last_current_position = float(y4)  # plan için güncel x0

        s1 = parameters[6]
        s2 = parameters[7]
        s3 = parameters[8]

        # OPERATION sekmesine veri yay
        self.bus.newTimedData.emit(
            float(y1), float(y2), float(y3), float(y4),
            float(s1), float(s2), float(s3),
            float(t_rel)
        )

        # Enable durumunu UI'a yansıt
        enable_state = parameters[0]
        self.bus.enableStateUpdated.emit(enable_state)

        # --- S-Curve aktifse: ramp step ve setpoint gönder ---
        if self._s_curve_enabled and (self._ramp is not None) and (not self._ramp.done()):
            try:
                sp = float(self._ramp.step())
                # Cihaza setpoint_position yaz
                Device.set_variables([Index_Joint.setpoint_position, sp])
            except Exception as e:
                print(f"[S-CURVE] step/send failed: {e}")

    def _on_tab_hook(self, index: int, name: str):
        if name == "OPERATION":
            Device.enter_operation()
            # OPERATION panel tablolarını cihazdan güncelle
            self.operationTab.reload_from_device()
        else:
            Device.enter_configuration()
        print(f"[HOOK] Entered tab {index}: {name} (ID={self.current_id})")

    # ------- CONFIG/OPERATION SET Kancaları -------
    def _on_config_param_set(self, name: str, value: str):
        Device.set_variables([Index_Joint[name], int(value)])
        print(f"[CONFIG SET] {name} = {value} | ID={self.current_id}")

    def _on_operation_param_set(self, panel_id: int, name: str, value: str):
        """
        Not: S-Curve açıkken position_setpoint kullanıcı tarafından girilemez (UI'da disable).
        Diğer paneller (current/velocity) normal çalışır.
        """
        try:
            idx = Index_Joint[name]
            v = float(value)
            if v.is_integer():
                v = int(v)
            Device.set_variables([idx, v])
            print(f"[OP SET] Panel {panel_id} | {name} = {v} , idx = {idx}| ID={self.current_id}")
        except Exception as e:
            print(f"[OP SET] FAIL: idx = {idx if 'idx' in locals() else '?'} , {panel_id} {name} {value} -> {e}")

    # ------- S-Curve event handlers -------
    def _on_scurve_toggled(self, checked: bool):
        self._s_curve_enabled = bool(checked)
        # UI: manuel position_setpoint girişini aç/kapat
        self.operationTab.panel3.set_extra_enabled(not self._s_curve_enabled)

        if not checked:
            # Kapandı -> planlayıcıyı bırak
            self._ramp = None
            print("[S-CURVE] Disabled and cleared ramp.")
            return

        # Açıldı; mevcut timer aralığına göre dt ayarla (saniye)
        dt = (self._op_timer.interval() / 1000.0) if self._op_timer.isActive() else 0.03

        # Ramp'i sadece bir kez yarat
        try:
            # Buradaki vmax/amax üst limit; asıl istek plan()'da vmax_des/a_des ile gelecek
            self._ramp = Ramp(dt=dt, vmax=MOTOR_VEL_MAX_IN_ENC_TYPE, amax=MOTOR_ACC_MAX_IN_ENC_TYPE)
            print(f"dt 1 = {dt}")
            print("[S-CURVE] Enabled (created Ramp once).")
        except Exception as e:
            print(f"[S-CURVE] Ramp init failed: {e}")


    def _on_scurve_plan_requested(self, target: float, vmax: float, a_des: float, t_des: float):
        """
        Kullanıcı 'Plan' dediğinde ya da target_position Enter ile girildiğinde çağrılır.
        x0 = son okunan current_position
        """
        if not self._s_curve_enabled:
            print("[S-CURVE] Plan requested but S-Curve is disabled.")
            return

        try:
            dt = (self._op_timer.interval() / 1000.0) if self._op_timer.isActive() else 0.03
            print(f"dt 2 = {dt}")
            if self._ramp is None:
                # Normalde buraya düşülmez; yine de güvenlik için:
                self._ramp = Ramp(dt=dt, vmax=MOTOR_VEL_MAX_IN_ENC_TYPE, amax=MOTOR_ACC_MAX_IN_ENC_TYPE)
                print("ERROR RAMP RECREATE")
            else:
                # Aynı ramp nesnesini koru; sadece parametrelerini güncelle
                try:
                    self._ramp.dt = dt
                except Exception:
                    pass
                # Eğer Ramp sınıfı bu alanları public tutuyorsa güncelle:
                try:
                    self._ramp.vmax = MOTOR_VEL_MAX_IN_ENC_TYPE
                    self._ramp.amax = MOTOR_ACC_MAX_IN_ENC_TYPE
                except Exception:
                    # Public değilse sorun değil; plan() içindeki vmax_des/a_des zaten kullanılacak
                    pass

            x0 = float(self._last_current_position)
            xg = float(target)
            t_d = float(t_des)
            a_d = rpm_to_tick_per_second(float(a_des))  # conversion for unit (rpm/s)
            v_d = rpm_to_tick_per_second(float(vmax))   # conversion for unit (rpm)

            # Asıl hedef/istekler plan'a gidiyor
            self._ramp.plan(x0=x0, xg=xg, t_des=t_d, a_des=a_d, vmax_des=v_d)
            print(f"[S-CURVE] Planned: x0={x0}, xg={xg}, t_des={t_d}, a_des={a_d}, vmax_des={v_d}, dt={dt}")
            print(f"t = {self._ramp.t}, a = {self._ramp.a}, dir ={self._ramp.dir}")
            print(f"t1 = {self._ramp.t1}, t2 = {self._ramp.t2}, vp = {self._ramp.Vp}")
        except Exception as e:
            print(f"[S-CURVE] Plan failed: {e}")

    # ------- Sağ Buton Kancaları (CONFIG) -------
    def _on_refresh_clicked(self):
        for var in self.configTab.parameters:
            var["value"] = Device.get_variables(Index_Joint[var["name"]])[0]
            print(var["value"])
        print(f"[BTN] Refresh | ID={self.current_id}")

        self.configTab.refresh_from_device(self.configTab.parameters)

    def _on_restart_clicked(self):
        Device.reboot()
        print(f"[BTN] Restart | ID={self.current_id}")

    def _on_config_save_clicked(self):
        Device.eeprom_save()
        print(f"[BTN] Config Save | ID={self.current_id}")

    def _on_config_reset_clicked(self):
        Device.factory_reset()
        print(f"[BTN] Apply | ID={self.current_id}")

    # (Opsiyonel) ID değiştirme API’sı
    def change_id(self, new_id: str):
        self.current_id = new_id
        self.bus.idChanged.emit(new_id)
        print(f"[INFO] Active ID changed to {new_id}")
        # TODO: ID değişince yapılacak işler (örn. port yeniden açma)

    def _on_enable_toggled(self, is_on: bool):
        try:
            Device.set_variables([Index_Joint.Enable, 1 if is_on else 0])
            print(f"[OP ENABLE] -> {is_on}")
        except Exception as e:
            print(f"[OP ENABLE] FAIL -> {e}")
            # Hata olursa UI’yı geri çevir
            self.operationTab.set_enable_ui(not is_on)


# =========================
#  Uygulama Başlatma Akışı
# =========================
def pre_start_handshake(device_id: str) -> bool:
    try:
        dev = Joint(int(device_id), port)
    except Exception:
        return False
    print(f"[PRE-START] Handshake with ID={device_id}...")
    return dev.ping()


def main():
    app = QtWidgets.QApplication([])
    # 1) Başlangıçta dialog göster
    while True:
        dlg = StartupDialog()
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        device_id = dlg.id_value or ""
        # 2) PRE-START HOOK (Handshake)
        ok = pre_start_handshake(device_id)
        if ok:
            break
        else:
            QtWidgets.QMessageBox.critical(
                None, "Bağlantı Hatası",
                f"ID={device_id} için ön iletişim başarısız. Lütfen tekrar deneyin."
            )
    Device._id = int(device_id)
    # 3) Ana pencereyi aç (CONFIG sekmesi ile başlayacak)
    win = MainWindow(device_id=device_id)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
