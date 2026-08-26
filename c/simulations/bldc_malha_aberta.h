#ifndef BLDC_MALHA_ABERTA_H
#define BLDC_MALHA_ABERTA_H

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <strings.h>
#include <getopt.h>

#include "structs.h"
#include "defs.h"

#include "PIcontroller.h"
#include "svpwm.h"
#include "inverter.h"
#include "transforms.h"
#include "bldc.h"
#include "VFstartup.h"
#include "progressbar.h"

#define VF_STARTUP_RAMP_TIME 300.f
#define VF_STARTUP_V_BOOST 1.0f
#define VF_STARTUP_V_PER_RAD_S 0.05f

int simulation_bldc_malha_aberta(sim_args_t *args)
{

    bldc_t motor =
        {
            .iabc = {0.0f, 0.0f, 0.0f},
            .eabc = {0.0f, 0.0f, 0.0f},

            .R = (float)args->R,
            .L = (float)args->L,
            .M = (float)args->M,
            .Ke = (float)args->Ke,

            .J = (float)args->J,
            .B = (float)args->B,
            .Te = 0.0f,

            .P = args->P,
            .Kt = (float)args->Kt,

            .theta_e = 0.0f,
            .theta_r = 0.0f,

            .omega_r = 0.0f,
            .omega_e = 0.0f,

        };


	double pwmTs = (1/args->Fsw) / 2.0f;
    /* O passo de integracao (dt) e derivado do periodo de chaveamento
     * (Ts = 1/Fsw), para que a comparacao com a portadora triangular
     * -- e portanto o chaveamento real do inversor -- seja resolvida
     * no tempo. Isso faz com que mudar Fsw realmente altere o
     * resultado da simulacao (ripple de corrente, torque, etc).
     * Se o usuario informar Dt explicitamente (> 0), ele sobrescreve
     * esse calculo automatico. */
    float dt;

    if (args->Dt > 0.0)
    {
        dt = (float)args->Dt;

        if (dt > pwmTs / 2.0f)
        {
            fprintf(stderr,
                    "Aviso: Dt=%.6e s e maior que metade do periodo de "
                    "chaveamento (Ts=%.6e s). O chaveamento real do "
                    "inversor NAO sera resolvido corretamente; considere "
                    "um Dt menor ou omita -d/--dt para o calculo "
                    "automatico (Ts/PwmSamples).\n\n",
                    (double)dt, (double)pwmTs);
        }
    }
    else
    {
        dt = pwmTs / (float)args->PwmSamples;
    }

    time_simulation_t time_sim =
        {
            .t0 = (float)args->Ti,
            .tf = (float)args->Tf,
            .dt = dt,
        };

    long total_steps =
        (long)((double)(time_sim.tf - time_sim.t0) / (double)dt + 0.5) + 1;

    printf("Periodo de chaveamento (Ts) = %.9e s\n", (double)pwmTs);
    printf("Passo de integracao (dt)    = %.9e s\n", (double)dt);
    printf("Total de passos da simulacao ~ %ld\n\n", total_steps);

    if (total_steps > 5000000L)
    {
        fprintf(stderr,
                "Aviso: %ld passos -- a simulacao pode demorar bastante. "
                "Reduza --pwm-samples ou aumente --fsw se necessario.\n\n",
                total_steps);
	}

    /* --------------------------------------------------------------
     *   PARTIDA V/F EM MALHA ABERTA (angulo sintetico)
     * --------------------------------------------------------------
     * O alvo de frequencia eletrica e derivado da referencia de
     * velocidade mecanica informada (args->rpm), multiplicada pelo
     * numero de pares de polos: omega_e_target = P * omega_r_ref.
     * A rampa dura VF_STARTUP_RAMP_TIME segundos.
     *
     * V_max respeita a regiao linear do modulador (Vdc/sqrt(3));
     * aqui usa-se uma margem extra (Vdc/1.8) para nao encostar no
     * limite durante a rampa, ja que aqui NAO ha SVPWM/chaveamento
     * -- o vetor alpha-beta e aplicado como fonte ideal.
     */
    float omega_r_ref = rpm_to_rads((float)args->rpm);
    float vf_omega_e_target = omega_r_ref * (float)motor.P;
    float vf_ramp_rate = vf_omega_e_target / VF_STARTUP_RAMP_TIME;

    printf("Partida V/F: alvo = %.6f rad/s eletrico (%.6f rad/s mecanico), "
           "rampa em %.3f s\n",
           vf_omega_e_target, omega_r_ref, VF_STARTUP_RAMP_TIME);

    vf_startup_t vf;
    vf_startup_init(&vf,
                    VF_STARTUP_V_BOOST,
                    VF_STARTUP_V_PER_RAD_S,
                    (float)args->Vdc / 1.8f,
                    vf_ramp_rate,
                    vf_omega_e_target);

    /* --------------------------------------------------------------
     *   ARQUIVO DE LOG
     * -------------------------------------------------------------- */
    const char *filename = args->filename;
    FILE *log_file = fopen(filename, "w");

    if (log_file == NULL)
    {
        perror("Erro ao criar o arquivo de log");
        return EXIT_FAILURE;
    }

 fprintf(log_file,
            "time;Va;Vb;Vc;ia;ib;ic;ea;eb;ec;id;iq;Te;theta_r;"
            "omega_r;theta_e_sintetico;omega_e_cmd;v_amp;vf_done\n");

	/* --------------------------------------------------------------
     *   PROGRESS BAR
     * -------------------------------------------------------------- */
	progress_bar_t pb;
	progress_bar_init(&pb, time_sim.t0, time_sim.tf, time_sim.dt);

    /* --------------------------------------------------------------
     *   LACO DE SIMULACAO
     * -------------------------------------------------------------- */
    for (long k = 0; k < total_steps; k++)
    {
		float t = time_sim.t0 + (float)((double)k * (double)dt);
        if (t > time_sim.tf)
            break;

        float Vabc[3];
        float v_alpha, v_beta, theta_e_synth;

        /* A. Rampa V/F: gera angulo eletrico SINTETICO (nao vem do
         *    rotor real) e o vetor de tensao alpha-beta */
        bool vf_done = vf_startup_step(&vf, dt, &theta_e_synth,
                                       &v_alpha, &v_beta);

        /* B. Transformada inversa de Clarke: alpha-beta -> abc */
        clarke_inverse_transform(v_alpha, v_beta,
                                 &Vabc[0], &Vabc[1], &Vabc[2]);

        /* C. Atualizacao da planta (motor BLDC) -- o motor "nao sabe"
         *    que o angulo aplicado e sintetico; a posicao real
         *    (motor.theta_r) evolui de acordo com a dinamica
         *    eletromecanica real, podendo ou nao acompanhar o campo
         *    girante (risco de perda de sincronismo/stall) */
        bldc_step(Vabc, &motor, dt, (float)args->Tl, false);

        /* D. Observacao (id/iq): usa o angulo eletrico REAL
         *    (motor.theta_e, calculado por bldc_step a partir de
         *    motor.theta_r) apenas para fins de log/diagnostico --
         *    NAO realimenta nada nesta malha aberta */
        float i_alpha, i_beta, i_d = 0.0f, i_q = 0.0f;
        clarke_transform(motor.iabc[0], motor.iabc[1], motor.iabc[2],
                         &i_alpha, &i_beta);
        park_transform(i_alpha, i_beta, motor.theta_e, &i_d, &i_q);

        float v_amp = vf.V_boost + vf.V_per_rad_s * fabsf(vf.omega_e_cmd);
        if (v_amp > vf.V_max) v_amp = vf.V_max;

		progress_bar_update(&pb, t);

		/* E. Log dos dados */
        fprintf(log_file,
                "%.6f;%.3f;%.3f;%.3f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f"
                ";%.4f;%.4f;%.4f;%.3f;%.4f;%.4f;%.4f;%d\n",
                t,
                Vabc[0], Vabc[1], Vabc[2],
                motor.iabc[0], motor.iabc[1], motor.iabc[2],
                motor.eabc[0], motor.eabc[1], motor.eabc[2],
                i_d, i_q,
                motor.Te,
                motor.theta_r, motor.omega_r,
                theta_e_synth, vf.omega_e_cmd, v_amp,
                (int)vf_done);
	}

	progress_bar_finish(&pb);

	return EXIT_SUCCESS;
}

#endif
