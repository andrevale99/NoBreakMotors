import numpy as np
import matplotlib.pyplot as plt
import scipy as sc

from numpy import pi

# --- Parametros do motor ---
R  = 0.5              # Ohm       - resistencia de armadura
L  = 0.3e-3           # H         - indutancia de magnetizacao
M  = 0.0              # H         - indutancia mutua (nao usada em bldc_step)
Ke = 0.00909483       # V/(rad/s) - constante eletrica (FCEM)
J  = 1.0e-4           # kg.m^2    - momento de inercia do rotor
B  = 5e-5             # N.m/(rad/s) - coeficiente de atrito viscoso
Tl = 0.0              # N.m       - torque de carga aplicado ao eixo
P  = 7                # -         - numero de pares de polos
Kt = 0.00909483       # N.m/A     - constante de torque


