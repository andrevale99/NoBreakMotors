import shutil, sys, time as time_mod
from dataclasses import dataclass

RESERVED_COLS = 55
MIN_WIDTH = 10
MAX_WIDTH = 100
FALLBACK_WIDTH = 80
LOG_MILESTONE_STEP = 5

@dataclass
class ProgressBar:
    t0: float = 0.0; tf: float = 0.0; dt: float = 0.0
    total_steps: int = 1
    current_step: int = 0
    last_percent: int = -1
    last_milestone: int = -1
    is_tty: bool = False
    bar_width: int = MIN_WIDTH
    start_clock: float = 0.0

def _fmt(seconds):
    seconds = max(seconds, 0.0)
    h = int(seconds//3600); m = int((seconds-h*3600)//60); s = int(seconds-h*3600-m*60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def progress_bar_init(t0, tf, dt):
    pb = ProgressBar(t0=t0, tf=tf, dt=dt)
    pb.total_steps = max(1, int((tf-t0)/dt + 0.5) + 1)
    pb.is_tty = sys.stdout.isatty()
    term_width = shutil.get_terminal_size((FALLBACK_WIDTH, 20)).columns
    pb.bar_width = min(max(term_width - RESERVED_COLS, MIN_WIDTH), MAX_WIDTH)
    pb.start_clock = time_mod.monotonic()
    if not pb.is_tty:
        print(f"Progresso da simulacao (saida nao interativa detectada; reportando a cada {LOG_MILESTONE_STEP}%):")
    return pb

def progress_bar_update(pb, t_current):
    step = int((t_current - pb.t0)/pb.dt + 0.5)
    pb.current_step = max(0, min(step, pb.total_steps))

    percent = int(100*pb.current_step/pb.total_steps)
    if percent == pb.last_percent:
        return
    pb.last_percent = percent

    elapsed = time_mod.monotonic() - pb.start_clock
    eta = elapsed*(pb.total_steps-pb.current_step)/pb.current_step if pb.current_step > 0 else 0.0

    if not pb.is_tty:
        if percent < pb.last_milestone + LOG_MILESTONE_STEP and percent != 100:
            return
        pb.last_milestone = percent
        print(f"  {percent:3d}% ({pb.current_step}/{pb.total_steps}) decorrido {_fmt(elapsed)} ETA {_fmt(eta)}")
        sys.stdout.flush()
        return

    filled = min(int(percent/100.0*pb.bar_width), pb.bar_width)
    bar = "#"*filled + "-"*(pb.bar_width-filled)
    print(f"\r[{bar}] {percent:3d}% ({pb.current_step}/{pb.total_steps}) decorrido {_fmt(elapsed)} ETA {_fmt(eta)}", end="")
    sys.stdout.flush()

def progress_bar_finish(pb):
    pb.current_step = pb.total_steps
    pb.last_percent = 100
    elapsed = time_mod.monotonic() - pb.start_clock
    if not pb.is_tty:
        print(f"  100% ({pb.total_steps}/{pb.total_steps}) concluido em {_fmt(elapsed)}")
    else:
        bar = "#"*pb.bar_width
        print(f"\r[{bar}] 100% ({pb.total_steps}/{pb.total_steps}) concluido em {_fmt(elapsed)}")
    sys.stdout.flush()