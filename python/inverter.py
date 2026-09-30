from dataclasses import dataclass

@dataclass
class Inverter:
    Vdc: float

def inverter_clamp(value, min_, max_):
    return max(min_, min(value, max_))

def inverter_duty_to_pole_voltage(inverter, duty):
    return duty * inverter.Vdc

def inverter_output_voltage(inverter, duty_a, duty_b, duty_c):
    duty_a = inverter_clamp(duty_a, 0.0, 1.0)
    duty_b = inverter_clamp(duty_b, 0.0, 1.0)
    duty_c = inverter_clamp(duty_c, 0.0, 1.0)

    Va = inverter_duty_to_pole_voltage(inverter, duty_a)
    Vb = inverter_duty_to_pole_voltage(inverter, duty_b)
    Vc = inverter_duty_to_pole_voltage(inverter, duty_c)
    Vn = (Va + Vb + Vc) / 3.0

    return [Va - Vn, Vb - Vn, Vc - Vn]