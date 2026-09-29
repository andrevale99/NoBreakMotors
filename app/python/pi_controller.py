import math
from dataclasses import dataclass

PI_NO_LIMIT_MIN = -math.inf
PI_NO_LIMIT_MAX = math.inf

@dataclass
class PIController:
    Kp: float
    Ki: float
    Ts: float
    has_min: bool = False
    has_max: bool = False
    output_min: float = PI_NO_LIMIT_MIN
    output_max: float = PI_NO_LIMIT_MAX
    integral: float = 0.0
    error: float = 0.0

def pi_controller_init(Kp, Ki, Ts, has_min, output_min, has_max, output_max):
    return PIController(
        Kp=Kp, Ki=Ki, Ts=Ts, has_min=has_min, has_max=has_max,
        output_min=output_min if has_min else PI_NO_LIMIT_MIN,
        output_max=output_max if has_max else PI_NO_LIMIT_MAX,
    )

def pi_controller_reset(pid):
    pid.integral = 0.0

def pi_controller_update(pid, reference, feedback):
    pid.error = reference - feedback
    proportional = pid.Kp * pid.error
    pid.integral += pid.Ki * pid.error * pid.Ts
    output = proportional + pid.integral

    if pid.has_min and output < pid.output_min:
        output = pid.output_min
        if pid.error < 0.0:
            pid.integral -= pid.Ki * pid.error * pid.Ts

    if pid.has_max and output > pid.output_max:
        output = pid.output_max
        if pid.error > 0.0:
            pid.integral -= pid.Ki * pid.error * pid.Ts

    return output