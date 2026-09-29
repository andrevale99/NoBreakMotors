import math
from dataclasses import dataclass
from transforms import clarke_inverse_transform

TWO_PI = 2*math.pi

@dataclass
class SVPWM:
    Vdc: float = 0.0
    Ts: float = 0.0
    Hz: float = 0.0

@dataclass
class SVPWMSector:
    magnitude: float
    angle: float
    sector: int

def svpwm_clamp(value, min_, max_):
    return max(min_, min(value, max_))

def svpwm_init(Hz, Ts, Vdc):
    if Vdc <= 0.0 or (Ts <= 0.0 and Hz <= 0.0):
        return None
    if Ts == 0.0:
        Ts = 1.0/Hz
    if Hz == 0.0:
        Hz = 1.0/Ts
    return SVPWM(Vdc=Vdc, Ts=Ts, Hz=Hz)

def svpwm_modulate(svpwm, Valpha, Vbeta):
    Va_ref, Vb_ref, Vc_ref = clarke_inverse_transform(Valpha, Vbeta)
    Vmax = max(Va_ref, Vb_ref, Vc_ref)
    Vmin = min(Va_ref, Vb_ref, Vc_ref)
    Voffset = -0.5*(Vmax + Vmin)

    duty_a = svpwm_clamp((Va_ref+Voffset)/svpwm.Vdc + 0.5, 0.0, 1.0)
    duty_b = svpwm_clamp((Vb_ref+Voffset)/svpwm.Vdc + 0.5, 0.0, 1.0)
    duty_c = svpwm_clamp((Vc_ref+Voffset)/svpwm.Vdc + 0.5, 0.0, 1.0)
    return duty_a, duty_b, duty_c

def svpwm_get_sector(alpha, beta):
    magnitude = math.hypot(alpha, beta)
    angle = math.atan2(beta, alpha)
    if angle < 0.0:
        angle += TWO_PI
    sector = min(int(angle/(math.pi/3.0)) + 1, 6)
    return SVPWMSector(magnitude, angle, sector)

def svpwm_carrier(svpwm, t):
    phase = math.fmod(t, svpwm.Ts)/svpwm.Ts
    if phase < 0.0:
        phase += 1.0
    return 2.0*phase if phase < 0.5 else 2.0 - 2.0*phase

def svpwm_gate_state(duty, carrier):
    return 1 if duty > carrier else 0