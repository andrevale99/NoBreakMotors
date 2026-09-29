import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

def cnc_drilling_coupled_2dof(t, y, params):
    """
    Sistema de EDOs para o modelo acoplado de 2 Graus de Liberdade (Axial-Torsional)
    y = [u, v, phi, omega]
    Onde:
    - u: Deslocamento axial da broca (Eixo Z)
    - v: Velocidade axial (Taxa de penetração)
    - phi: Posição angular do fuso/broca
    - omega: Velocidade angular (Rotação)
    """
    # Parâmetros físicos do sistema
    M = params['M']              # Massa efetiva na direção axial (kg)
    J = params['J']              # Momento de inércia torsional do fuso/broca (kg.m^2)
    C_axial = params['C_axial']  # Amortecimento axial (N.s/m)
    K_axial = params['K_axial']  # Rigidez axial da estrutura (N/m)
    C_torsion = params['C_torsion'] # Amortecimento torsional (N.m.s/rad)
    K_torsion = params['K_torsion'] # Rigidez torsional (N.m/rad)
    
    # Entradas de controle da CNC
    WOB = params['WOB_func'](t)  # Força axial aplicada (Weight on Bit / Avanço)
    Tm = params['Tm_func'](t)    # Torque aplicado no fuso
    
    # Coeficientes de acoplamento na interface broca-material
    alpha = params['alpha']      # Acoplamento da velocidade axial no corte
    beta = params['beta']        # Acoplamento torsional
    
    u, v, phi, omega = y
    
    # Forças e torques resistivos decorrentes da interação com o material
    F_corte = alpha * v
    T_corte = beta * omega
    
    # 1. Equação de Movimento Axial (Eixo Z):
    # M * u_ddot + C_axial * v + K_axial * u = WOB - F_corte
    du_dt = v
    dv_dt = (WOB - F_corte - C_axial * v - K_axial * u) / M
    
    # 2. Equação de Movimento Torsional (Rotação do Fuso):
    # J * omega_dot + C_torsion * omega + K_torsion * phi = Tm - T_corte
    dphi_dt = omega
    domega_dt = (Tm - T_corte - C_torsion * omega - K_torsion * phi) / J
    
    return [du_dt, dv_dt, dphi_dt, domega_dt]

# Dicionário de parâmetros representativos para uma bancada/usinagem CNC
params = {
    'M': 4.5,              # Massa equivalente do eixo Z
    'J': 0.35,             # Inércia torsional do conjunto
    'C_axial': 25.0,       # Amortecimento axial
    'K_axial': 8000.0,     # Rigidez estrutural axial
    'C_torsion': 1.5,      # Amortecimento torsional
    'K_torsion': 300.0,    # Rigidez torsional do eixo
    'alpha': 20.0,         # Fator de resistência ao avanço
    'beta': 0.8,           # Fator de resistência ao torque de corte
    'WOB_func': lambda t: 200.0 if t >= 0.5 else 0.0,  # Aplicação de avanço em t = 0.5s
    'Tm_func': lambda t: 15.0 if t >= 0.5 else 0.0     # Aplicação de torque em t = 0.5s
}

# Condições iniciais [pos_axial, vel_axial, pos_angular, vel_angular]
y0 = [0.0, 0.0, 0.0, 0.0]

# Intervalo de simulação temporal
t_span = (0.0, 4.0)
t_eval = np.linspace(t_span[0], t_span[1], 1000)

# Resolução numérica do sistema acoplado
sol = solve_ivp(cnc_drilling_coupled_2dof, t_span, y0, args=(params,), t_eval=t_eval, method='RK45')

# Plotagem dos resultados dinâmicos acoplados
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.plot(sol.t, sol.y[0], label='Deslocamento Axial ($u$)', color='blue')
plt.xlabel('Tempo (s)')
plt.ylabel('Posição Axial / Z (m)')
plt.title('Dinâmica Axial (Eixo Z da CNC)')
plt.grid(True)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(sol.t, sol.y[3], label='Velocidade Angular ($\omega$)', color='darkorange')
plt.xlabel('Tempo (s)')
plt.ylabel('Velocidade Angular (rad/s)')
plt.title('Dinâmica Torsional (Fuso / Rotação)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()