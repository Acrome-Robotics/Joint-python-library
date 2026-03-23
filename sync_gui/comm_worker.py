"""
comm_worker.py  –  Background serial communication thread for Sync GUI
"""

import time
import datetime
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from acrome_joint.joint import Joint, Index_Joint, set_joint_variables_sync
from acrome_joint.serial_port import SerialPort


POLL_INTERVAL_MS = 50   # ms between individual joint polls


class CommWorker(QThread):
    """
    Runs in its own thread.
    Handles all serial I/O so the GUI thread stays responsive.
    """

    # ── Outgoing signals (→ GUI) ─────────────────────────────────────────
    data_ready        = pyqtSignal(int, list)   # joint_id, [9 values]
    timeout_event     = pyqtSignal(int)          # joint_id
    connection_status = pyqtSignal(bool, str)    # connected, message

    def __init__(self, parent=None):
        super().__init__(parent)

        self._mutex    = QMutex()
        self._port: SerialPort | None = None
        self._joints: list[Joint | None] = [None] * 4
        self._enables  = [False, False, False, False]  # which joints to poll
        self._running  = False

        # Pending commands (set from GUI thread, consumed in worker thread)
        self._pending_sync_drive: dict | None = None    # {joint_id: degrees}
        self._pending_torque: tuple | None = None       # (enabled: bool, [flags])

    # ------------------------------------------------------------------ #
    #  Connection management (called from GUI thread)
    # ------------------------------------------------------------------ #
    def connect_port(self, port_name: str, baudrate: int):
        try:
            p = SerialPort(port_name, baudrate=baudrate, timeout=0.1, isTest=False)
            joints = [Joint(i, p) for i in range(4)]
            with QMutexLocker(self._mutex):
                self._port   = p
                self._joints = joints
            print(f"[CONN] Bağlandı → {port_name} @ {baudrate} baud")
            self.connection_status.emit(True, f"Connected → {port_name} @ {baudrate}")
        except Exception as exc:
            print(f"[CONN] HATA: {exc}")
            self.connection_status.emit(False, f"Connection failed: {exc}")

    def disconnect_port(self):
        with QMutexLocker(self._mutex):
            if self._port:
                try:
                    self._port.close_port()
                except Exception:
                    pass
                self._port   = None
                self._joints = [None] * 4
        self.connection_status.emit(False, "Disconnected")

    # ------------------------------------------------------------------ #
    #  Slots called from GUI thread
    # ------------------------------------------------------------------ #
    def update_joint_enables(self, flags: list):
        with QMutexLocker(self._mutex):
            self._enables = list(flags)

    def send_sync_drive(self, setpoints: dict):
        """setpoints = {joint_id: degrees (float)}  – only enabled joints"""
        with QMutexLocker(self._mutex):
            self._pending_sync_drive = dict(setpoints)

    def send_torque_enable(self, enabled: bool, joint_enables: list):
        with QMutexLocker(self._mutex):
            self._pending_torque = (enabled, list(joint_enables))

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------ #
    #  Main loop
    # ------------------------------------------------------------------ #
    def run(self):
        self._running = True
        while self._running:
            with QMutexLocker(self._mutex):
                port    = self._port
                joints  = list(self._joints)
                enables = list(self._enables)

                sync_cmd   = self._pending_sync_drive
                torque_cmd = self._pending_torque
                self._pending_sync_drive = None
                self._pending_torque     = None

            if port is None:
                time.sleep(0.1)
                continue

            # ── Pending: Torque enable ────────────────────────────────
            if torque_cmd is not None:
                enabled, flags = torque_cmd
                pairs = [[i, enabled] for i in range(4) if flags[i]]
                if pairs:
                    ids = [p[0] for p in pairs]
                    print(f"[TORQUE] {'ENABLE' if enabled else 'DISABLE'} → Joint {ids}")
                    try:
                        set_joint_variables_sync(port, Index_Joint.Enable, *pairs)
                        print(f"[TORQUE] Gönderildi OK")
                    except Exception as e:
                        print(f"[TORQUE] HATA: {e}")
                else:
                    print("[TORQUE] Hiçbir joint enable değil, paket gönderilmedi.")

            # ── Pending: Sync Drive ───────────────────────────────────
            if sync_cmd is not None:
                pairs = [[jid, deg] for jid, deg in sync_cmd.items()]
                if pairs:
                    print(f"[SYNC DRIVE] Setpoint'ler → " +
                          ", ".join(f"J{p[0]}: {p[1]:.1f}°" for p in pairs))
                    try:
                        set_joint_variables_sync(
                            port,
                            Index_Joint.setpoint_position,
                            *pairs
                        )
                        print(f"[SYNC DRIVE] Gönderildi OK")
                    except Exception as e:
                        print(f"[SYNC DRIVE] HATA: {e}")

            # ── Polling: read status from each enabled joint ──────────
            for jid in range(4):
                if not enables[jid]:
                    continue
                joint = joints[jid]
                if joint is None:
                    continue
                ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                try:
                    result = joint.get_currentStatus_parameters()
                    if result and result[0] is not None:
                        pos  = result[4] if len(result) > 4 else '?'
                        vel  = result[3] if len(result) > 3 else '?'
                        temp = result[5] if len(result) > 5 else '?'
                        print(f"[{ts}] [POLL J{jid}] pos={pos:.2f}°  vel={vel:.2f}  temp={temp:.1f}°C")
                        self.data_ready.emit(jid, result)
                    else:
                        print(f"[{ts}] [POLL J{jid}] TIMEOUT / boş yanıt")
                        self.timeout_event.emit(jid)
                except Exception as e:
                    print(f"[{ts}] [POLL J{jid}] HATA: {e}")
                    self.timeout_event.emit(jid)

                time.sleep(POLL_INTERVAL_MS / 1000.0)

            # Small sleep when no joints enabled to avoid busy loop
            if not any(enables):
                time.sleep(0.1)
