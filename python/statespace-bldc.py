"""
statespace-bldc.py

Simulacao do motor BLDC em espaco de estados (malha aberta), em Python,
equivalente ao modelo implementado em C em bldc.h (bldc_step()).

Estado: x = [ia, ib, ic, omega_r, theta_r]

Equacoes eletricas (por fase):
    di/dt = (V - R*i - e) / L
    e = Ke * omega_e * f(theta_e + phi)      # f = forma de onda da FCEM

Equacoes mecanicas:
    Te = Kt * (ia*fa + ib*fb + ic*fc)
    domega_r/dt = (Te - Tl - B*omega_r) / J
    dtheta_r/dt = omega_r

Integracao: Euler explicito.

Neste script, a tensao Vabc e sintetizada de forma sincronizada com o
proprio angulo eletrico do rotor (equivalente a assumir um sensor de
posicao ideal e comutacao perfeita, sem inversor/PWM real e sem malha
de controle) -- util para validar a planta antes de acoplar
SVPWM/inversor/controladores, como feito em main.c.
"""

import numpy as np
import matplotlib.pyplot as plt

# --- Parametros do motor ---
R = 0.5              # Ohm       - resistencia de armadura
L = 0.3e-3            # H         - indutancia de magnetizacao
M = 0.0               # H         - indutancia mutua
Ke = 0.00909483       # V/(rad/s) - constante eletrica (FCEM)
J = 1.0e-4            # kg.m^2    - momento de inercia do rotor
B = 5e-5              # N.m/(rad/s) - coeficiente de atrito viscoso
Tl = 0.0              # N.m       - torque de carga aplicado ao eixo
P = 7                 # -         - numero de pares de polos
Kt = 0.00909483       # N.m/A     - constante de torque

Vdc = 12.0
Va = Vdc / np.sqrt(3.0)

L_eff = L - M         # indutancia efetiva (M = 0 aqui, mas mantido por generalidade)

TWO_PI = 2.0 * np.pi

PHI_A = 0.0
PHI_B = -2.0 * np.pi / 3.0
PHI_C = 2.0 * np.pi / 3.0

# --- Configuracao temporal ---
t0 = 0.0
tf = 0.3
dt = 1e-6

samples = int((tf - t0) / dt)
time = np.linspace(t0, tf, samples)

# --- Vetores de estado / log ---
iabc = np.zeros((samples, 3))
omega_r = np.zeros(samples)
theta_r = np.zeros(samples)
Te = np.zeros(samples)


def back_emf_shape(theta, phi):
    """Forma de onda senoidal normalizada da FCEM (equivalente ao
    trapezoidal_back_emf() do bldc.h, mas para o caso senoidal)."""
    return np.sin(theta + phi)


# --- Laco de integracao (Euler explicito) ---
for k in range(samples - 1):

    theta_e = (P * theta_r[k]) % TWO_PI
    omega_e = P * omega_r[k]

    fabc = np.array([
        back_emf_shape(theta_e, PHI_A),
        back_emf_shape(theta_e, PHI_B),
        back_emf_shape(theta_e, PHI_C),
    ])

    # Fonte de tensao sincronizada com o rotor (malha aberta ideal;
    # substitua por Vabc vindo do inversor/SVPWM quando acoplar o
    # controlador, como e feito em main.c)
    Vabc = Va * fabc

    eabc = Ke * omega_e * fabc

    diabc = (Vabc - R * iabc[k] - eabc) / L_eff

    iabc[k + 1] = iabc[k] + diabc * dt

    Te[k] = Kt * np.dot(iabc[k], fabc)

    domega_r = (Te[k] - Tl - B * omega_r[k]) / J
    omega_r[k + 1] = omega_r[k] + domega_r * dt
    theta_r[k + 1] = theta_r[k] + omega_r[k] * dt

# ultimo ponto de torque (nao calculado dentro do laco, por causa do k+1)
Te[-1] = Kt * np.dot(
    iabc[-1],
    np.array([
        back_emf_shape((P * theta_r[-1]) % TWO_PI, PHI_A),
        back_emf_shape((P * theta_r[-1]) % TWO_PI, PHI_B),
        back_emf_shape((P * theta_r[-1]) % TWO_PI, PHI_C),
    ]),
)

# --- Graficos ---
fig, axs = plt.subplots(3, 1, figsize=(9, 8), sharex=True)

axs[0].plot(time, iabc[:, 0], label="ia")
axs[0].plot(time, iabc[:, 1], label="ib")
axs[0].plot(time, iabc[:, 2], label="ic")
axs[0].set_ylabel("Corrente [A]")
axs[0].legend()
axs[0].grid(True)

axs[1].plot(time, omega_r * 60.0 / TWO_PI)
axs[1].set_ylabel("Velocidade [rpm]")
axs[1].grid(True)

axs[2].plot(time, Te)
axs[2].set_ylabel("Torque [N.m]")
axs[2].set_xlabel("Tempo [s]")
axs[2].grid(True)

plt.tight_layout()
plt.show()
