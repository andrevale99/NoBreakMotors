import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_CSV = "closedloop_simulation.csv"
DEFAULT_PASTA = "img/"
DEFAULT_FIGSIZE = (15, 10)


plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.serif": ["cmr10", "DejaVu Serif", "serif"],
    "axes.formatter.use_mathtext": True,

    # Fontes
    "font.size": 18,
    "axes.titlesize": 18,
    "axes.labelsize": 18,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 18,
    "figure.titlesize": 22,

    # Espessura dos eixos
    "axes.linewidth": 1.2,

    # Tamanho dos ticks
    "xtick.major.size": 6,
    "ytick.major.size": 6,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
})


# arq = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
# pasta_saida = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASTA


# ============================================================
# AUXILIARES
# ============================================================

def no_xlabel():
    plt.tick_params(axis="x", labelbottom=False)


# ============================================================
# Função FFT
# ============================================================

def calcular_fft(sinal, Fs):
    N = len(sinal)

    # Remove componente DC
    sinal = sinal - np.mean(sinal)

    # Janela de Hann
    janela = np.hanning(N)

    sinal = sinal * janela

    # FFT
    fft = np.fft.rfft(sinal)

    # Correção da amplitude
    amplitude = 2 * np.abs(fft) / np.sum(janela)

    frequencia = np.fft.rfftfreq(N, d=1 / Fs)

    return frequencia, amplitude


# ============================================================
# Gráficos da FFT
# ============================================================

def plot_fft(simulation_file_csv=None):

    if simulation_file_csv is None:
        print("Sem arquivo de dados")
        return -1

    arquivo = simulation_file_csv

    df = pd.read_csv(arquivo, sep=";")

    # Nome da coluna de tempo
    tempo = df["time"].values

    # Correntes trifásicas
    ia = df["ia"].values
    ib = df["ib"].values
    ic = df["ic"].values

    # ========================================================
    # Frequência de amostragem
    # ========================================================

    Ts = np.mean(np.diff(tempo))
    Fs = 1 / Ts
    f_max = 50000

    print(f"Fs = {Fs / 1e6:.2f} MHz")
    print(f"Nyquist = {Fs / 2:.1f} kHz")
    print(f"Resolução = {Fs / len(ia):.2f} Hz")

    # ========================================================
    # FFT das três correntes
    # ========================================================

    f_ia, A_ia = calcular_fft(ia, Fs)
    f_ib, A_ib = calcular_fft(ib, Fs)
    f_ic, A_ic = calcular_fft(ic, Fs)

    # ========================================================
    # Limita até f_max
    # ========================================================

    idx = f_ia <= f_max

    # ========================================================
    # Plota
    # ========================================================

    plt.figure(figsize=(12, 7))

    plt.plot(f_ia[idx], A_ia[idx], label="Ia")
    plt.plot(f_ib[idx], A_ib[idx], label="Ib")
    plt.plot(f_ic[idx], A_ic[idx], label="Ic")

    plt.title("FFT das Correntes Trifásicas")
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Amplitude (A)")
    plt.xlim(0, f_max)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(DEFAULT_PASTA + "fft_correntes_tabc.pdf")


# ============================================================
# FUNÇÃO PRINCIPAL DE PLOTAGEM
# ============================================================

def plot_graficos(simulation_file_csv=None):

    if simulation_file_csv is None:
        print("Sem arquivo CSV da simulacao")
        return -1

    arq = simulation_file_csv
    pasta_saida = DEFAULT_PASTA

    str_time = "time"
    str_va = "Va"
    str_vb = "Vb"
    str_vc = "Vc"
    str_ia = "ia"
    str_ib = "ib"
    str_ic = "ic"
    str_ea = "ea"
    str_eb = "eb"
    str_ec = "ec"
    str_id = "id"
    str_iq = "iq"
    str_te = "Te"
    str_thetar = "theta_r"
    str_omegar = "omega_r"
    str_iqref = "iq_ref"
    str_vdref = "vd_ref"
    str_vqref = "vq_ref"
    str_theta_e_sintetico = "theta_e_sintetico"
    str_omega_e_cmd = "omega_e_cmd"
    str_v_amp = "v_amp"

    # ========================================================
    # Leitura dos dados
    # ========================================================

    data = pd.read_csv(arq, sep=";")

    time = data[str_time]

    vabc = np.array([
        data[str_va],
        data[str_vb],
        data[str_vc]
    ])

    iabc = np.array([
        data[str_ia],
        data[str_ib],
        data[str_ic]
    ])

    eabc = np.array([
        data[str_ea],
        data[str_eb],
        data[str_ec]
    ])

    iq = data[str_iq]
    _id = data[str_id]
    te = data[str_te]
    omegar = data[str_omegar]

    rpm = omegar * 60.0 / (2 * np.pi)

    try:

        iqref = data[str_iqref]
        vdref = data[str_vdref]
        vqref = data[str_vqref]

        # ====================================================
        # Tempo x iabc, rpm
        # ====================================================

        plt.figure(figsize=DEFAULT_FIGSIZE)

        plt.subplot(211)
        plt.plot(time, iabc.T)
        plt.ylabel("A")
        plt.grid()
        no_xlabel()

        plt.subplot(212)
        plt.plot(time, rpm)
        plt.grid()
        plt.ylabel("RPM")
        plt.xlabel("s")

        plt.tight_layout()
        plt.savefig(pasta_saida + "01_corrente-rpm.pdf")

        # ====================================================
        # Tempo x iq, id, iqref, Te
        # ====================================================

        plt.figure(figsize=DEFAULT_FIGSIZE)

        plt.subplot(211)
        plt.plot(time, _id, label=r"$i_{d}$")
        plt.plot(time, iq, label=r"$i_{q}$")
        plt.plot(time, iqref, label=r"$i_{qref}$", ls="--")
        plt.ylabel("A")
        plt.grid()
        plt.legend()
        no_xlabel()

        plt.subplot(212)
        plt.plot(time, te)
        plt.grid()
        plt.ylabel("Nm")
        plt.xlabel("s")

        plt.tight_layout()
        plt.savefig(pasta_saida + "02_iq-id-Te.pdf")

    except:

        # ====================================================
        # Tempo x iabc, rpm, Te, iq, id
        # ====================================================

        plt.figure(figsize=DEFAULT_FIGSIZE)

        plt.subplot(211)
        plt.plot(time, iabc.T)
        plt.ylabel("A")
        plt.grid()
        no_xlabel()

        plt.subplot(212)
        plt.plot(time, rpm)
        plt.grid()
        plt.ylabel("RPM")
        plt.xlabel("s")

        plt.tight_layout()
        plt.savefig(pasta_saida + "01_corrente-rpm.pdf")

    plot_fft(simulation_file_csv)

    plt.show()