from math import sqrt

class Ramp:
    def __init__(self, dt=0.001, vmax=1.0, amax=1.0):
        self.dt, self.vmax, self.amax = dt, vmax, amax
        self.reset()

    def reset(self):
        self.x0 = self.xg = 0.0
        self.t = self.t1 = self.t2 = self.tp = 0.0
        self.Vp = self.a = 0.0
        self.dir = 1
        self._x = 0.0
        self._x_t1 = 0.0  # hızlanma fazında alınan mesafe (t1_pos)

    def plan(self, x0, xg, t_des=0.0, a_des=0.0, vmax_des=0.0):
        """Trajektoriyi hazırla; ardından step() her çağrıda bir sonraki setpoint'i üretir."""
        self.reset()
        self.x0, self.xg = x0, xg
        e = xg - x0
        self.dir = 1 if e >= 0 else -1
        e = abs(e)

        Vmax = self.vmax if (vmax_des <= 0 or vmax_des > self.vmax) else vmax_des
        acc  = self.amax if (a_des   <= 0 or a_des   > self.amax) else a_des

        # 1) ZAMAN+İVME verildiyse dene
        if t_des > 0 and acc > 0:
            D = t_des*t_des - 4.0*(e/acc)
            if D >= 0:
                t1 = (t_des - sqrt(D)) / 2.0  # her zaman <= t_des/2
                Vp = acc * t1
                if 0 <= t1 and Vp < Vmax:
                    t2 = t_des - 2.0*t1
                    self._finalize(t1, t2, Vp, acc)
                    return

        # 2) Sadece ZAMAN verildiyse
        if t_des > 0:
            if Vmax * t_des > e:
                Vp = 2.0*e / t_des
                if Vp <= Vmax:
                    t1, t2 = t_des/2.0, 0.0
                else:
                    t1 = t_des - e / Vmax
                    t2 = t_des - 2.0*t1
                    Vp = Vmax
                a = Vp / max(t1, 1e-12)
                self._finalize(t1, t2, Vp, a)
                return

        # 3) İVME (veya hiçbiri) verildiyse
        if acc <= 0:  # her ikisi de yoksa C kodundaki gibi varsayılan
            acc = Vmax / 2.0
        t1 = sqrt(e / acc)
        Vp = acc * t1
        if Vp > Vmax:
            t1 = Vmax / acc
            t2 = (e - Vmax*t1) / Vmax
            Vp = Vmax
        else:
            t2 = 0.0
        self._finalize(t1, t2, Vp, acc)

    def _finalize(self, t1, t2, Vp, a):
        self.t1, self.t2, self.Vp, self.a = t1, t2, Vp, a
        self.tp = 2.0*t1 + t2
        self._x = self.x0
        self._x_t1 = 0.5 * a * t1 * t1  # hızlanma mesafesi

    def step(self):
        """Bir kontrol tikinde bir sonraki setpoint."""
        t, a, d = self.t, self.a, self.dir
        x0, xg = self.x0, self.xg
        t1, t2, tp, Vp = self.t1, self.t2, self.tp, self.Vp

        if t < t1:  # hızlan
            x = x0 + 0.5 * a * t*t * d
        elif t < t1 + t2:  # sabit hız
            x = x0 + (self._x_t1 + Vp*(t - t1)) * d
        elif t < tp:  # yavaşla
            dt = tp - t
            x = xg - 0.5 * a * dt*dt * d
        else:
            x = xg

        # hedefi aşma koruması
        if (d > 0 and x > xg) or (d < 0 and x < xg):
            x = xg

        self._x = x
        self.t += self.dt
        return x

    def done(self):
        return self._x == self.xg
