import numpy as np
import matplotlib.pyplot as plt
import scipy as sc

from numpy import pi

def back_emf(theta, phi):
	return sin(theta_e + phi)

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

Vdc = 12
Va = 12 / np.sqrt(3)

L = L-M
RL = R / L

t0 = 0.0
tf = 0.3
dt = 1e-6

PHI_A = 0
PHI_B = -2*pi/3
PHI_C = 2*pi/3

samples = int((tf-t0)/dt)

time = np.linspace(t0,tf,samples)

diabc = np.zeros((3,Samples))
iabc = np.zeros((3,Samples))
wm = np.zeros(Samples)

for k in range(Samples):
	theta_e = wm[k]*P
	Vabc = np.array([[Va*np.sin(theta_e + PHI_A)],
					 [Va*np.sin(theta_e + PHI_B)],
					 [Va*np.sin(theta_e + PHI_C)]]) 
	
	diabc[k] = RL * (Vabc * ibc[k] - lambda_emf * np.array([[back_emf(theta_e, PHI_A)],
														   [back_emf(theta_e, PHI_B)],
														   [back_emf(theta_e, PHI_C)]]))

	
