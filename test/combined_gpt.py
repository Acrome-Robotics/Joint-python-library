import time
from acrome_joint.joint import *
from gui.ramp_trajectory import *   # <-- S-Curve Ramp sınıfını kullanacağız

# --- JOINT/PORT ---
keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.01)
joint_0 = Joint(0, port)
joint_1 = Joint(1, port)


# ------------------------------------------------------------
# Yardımcı: iki ekseni birlikte akıtma (Ramp SINIFINI KULLANIR)
# ------------------------------------------------------------
class TwoAxisStreamer:
    def __init__(self, joint0, joint1, dt=0.001,
                 vmax0=5000.0, amax0=20000.0,
                 vmax1=5000.0, amax1=20000.0):
        self.j0 = joint0
        self.j1 = joint1
        self.dt = dt

        # DIŞARIDAN GELEN Ramp SINIFI KULLANILIYOR
        self.r0 = Ramp(dt=dt, vmax=vmax0, amax=amax0)
        self.r1 = Ramp(dt=dt, vmax=vmax1, amax=amax1)

        # Başlangıç komutu (istersen gerçek pozisyonu okuyup bunları güncelle)
        self.last_cmd_0 = 0.0
        self.last_cmd_1 = 0.0

    def plan_to(self, xg0, xg1, t_des=0.0, a_des=0.0, vmax_des=0.0):
        """İki eksen için eşzamanlı plan hazırla (Ramp.plan kullanır)."""
        self.r0.plan(self.last_cmd_0, xg0, t_des=t_des, a_des=a_des, vmax_des=vmax_des)
        self.r1.plan(self.last_cmd_1, xg1, t_des=t_des, a_des=a_des, vmax_des=vmax_des)

    def stream_until_done(self, sleep_fn=time.sleep):
        """Plan bitene kadar her dt’de setpoint gönder (Ramp.step kullanır)."""
        idx = Index_Joint.setpoint_position
        while not (self.r0.done() and self.r1.done()):
            p0 = self.r0.step()
            p1 = self.r1.step()

            self.j0.set_variables([idx, p0])
            self.j1.set_variables([idx, p1])

            self.last_cmd_0 = p0
            self.last_cmd_1 = p1
            sleep_fn(self.dt)

    def goto(self, xg0, xg1, t_des=0.0, a_des=0.0, vmax_des=0.0):
        """Tek çağrıda planla + akıt."""
        self.plan_to(xg0, xg1, t_des=t_des, a_des=a_des, vmax_des=vmax_des)
        self.stream_until_done()

# ------------------------------------------------------------
# ÖRNEK AKIŞ
# ------------------------------------------------------------
if __name__ == "__main__":
    streamer = TwoAxisStreamer(
        joint0=joint_0, joint1=joint_1,
        dt=0.05,            # 20 Hz kontrol
        vmax0=5000.0, amax0=20000.0,
        vmax1=5000.0, amax1=20000.0
    )

    # 1) Zaman kısıtlı hareket (3 saniyede hedefe git)
    streamer.goto(xg0=10000.0, xg1=-8000.0, t_des=3.0)

    # 2) Sadece ivme/hız limitiyle (zaman vermezsen trapez profil)
    streamer.goto(xg0=0.0, xg1=0.0, a_des=15000.0, vmax_des=4000.0)

    # 3) Waypoint zinciri
    for (w0, w1) in [(5000, 5000), (10000, -2000), (3000, 9000), (0, 0)]:
        streamer.goto(xg0=w0, xg1=w1, a_des=20000.0, vmax_des=5000.0)
