/**
 * @file aasi_embedded.h
 * @brief Sovereign AASI RTOS Flight Interface Header
 * @details Conforming to RTCA DO-178C DAL-A, EUROCAE ED-12C, and ASTM F3269-21.
 *          Target Architecture: ARM Cortex-R5, Cortex-M4F, RISC-V Shakti / Vega.
 *          Zero dynamic allocations. Deterministic timing < 120 us.
 */

#ifndef AASI_EMBEDDED_H_
#define AASI_EMBEDDED_H_

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---------------------------------------------------------------------------
 * ASTM F3269-21 Run-Time Assurance Failsafe Codes (F-1 to F-19)
 * --------------------------------------------------------------------------- */
typedef enum {
    AASI_FAILSAFE_NOMINAL                       = 0,
    AASI_FAILSAFE_F1_INVALID_COGNITIVE_STAGE    = 1,
    AASI_FAILSAFE_F2_INVALID_ED25519_SIGNATURE  = 2,
    AASI_FAILSAFE_F3_MISSING_MANDATORY_FIELD    = 3,
    AASI_FAILSAFE_F4_MERKLE_PROVENANCE_MISMATCH = 4,
    AASI_FAILSAFE_F5_SAFETY_MONITOR_DISAGREE    = 5,
    AASI_FAILSAFE_F6_HEARTBEAT_LOSS_TIMEOUT     = 6,
    AASI_FAILSAFE_F7_RATE_OF_CLIMB_EXCEEDED     = 7,
    AASI_FAILSAFE_F8_ENVELOPE_KINEMATIC_VIOL    = 8,
    AASI_FAILSAFE_F9_ATTITUDE_LIMIT_EXCEEDED    = 9,
    AASI_FAILSAFE_F10_DYNAMIC_PRESSURE_LIMIT    = 10,
    AASI_FAILSAFE_F11_GEOFENCE_BREACHED         = 11,
    AASI_FAILSAFE_F12_ACTUATOR_SATURATION       = 12,
    AASI_FAILSAFE_F13_NAVIC_COVARIANCE_DIVERGE  = 13,
    AASI_FAILSAFE_F14_ECLIPSE_GNSS_OUTAGE       = 14,
    AASI_FAILSAFE_F15_ISL_LINK_LOST             = 15,
    AASI_FAILSAFE_F16_THRUSTER_PLUME_CONTAM     = 16,
    AASI_FAILSAFE_F17_RELATIVE_VELOCITY_EXCESS  = 17,
    AASI_FAILSAFE_F18_THERMAL_EXCEEDANCE        = 18,
    AASI_FAILSAFE_F19_BATTERY_DEPTH_DISCHARGE   = 19,
} aasi_failsafe_code_t;

/* ---------------------------------------------------------------------------
 * C-ABI Structures
 * --------------------------------------------------------------------------- */
typedef struct {
    uint32_t is_authorized;         /* 1 = Authorized, 0 = Intercepted */
    uint32_t failsafe_code;         /* aasi_failsafe_code_t */
    uint32_t channel_agreement;     /* 2-of-3 voting score (1..3) */
    uint32_t execution_time_us;     /* Measured microsecond latency */
} aasi_rta_verdict_t;

/* ---------------------------------------------------------------------------
 * Native Flight Function Signatures
 * --------------------------------------------------------------------------- */

/**
 * @brief Evaluates flight control commands against ASTM F3269-21 safety monitor.
 * @param aileron_cmd Normalized command [-1.0, 1.0]
 * @param elevator_cmd Normalized command [-1.0, 1.0]
 * @param rudder_cmd Normalized command [-1.0, 1.0]
 * @param current_roll_rad Current airframe roll in radians
 * @param current_pitch_rad Current airframe pitch in radians
 * @param current_airspeed_mps Indicated airspeed in m/s
 * @return Verdict indicating whether actuation is permitted or overridden
 */
aasi_rta_verdict_t aasi_rta_evaluate(
    float aileron_cmd,
    float elevator_cmd,
    float rudder_cmd,
    float current_roll_rad,
    float current_pitch_rad,
    float current_airspeed_mps
);

/**
 * @brief Propagates 12-state NavIC Relative Orbit EKF using Clohessy-Wiltshire dynamics.
 * @param state_inout Pointer to double[12] state vector [x, y, z, vx, vy, vz, b0..2, bias0..2]
 * @param dt_sec Propagation time step in seconds
 * @param mean_motion Orbital mean motion n = sqrt(mu / a^3) in rad/s
 * @return 0 on success, negative error code on null pointer
 */
int32_t aasi_ekf_propagate(
    double *state_inout,
    double dt_sec,
    double mean_motion
);

#ifdef __cplusplus
}
#endif

#endif /* AASI_EMBEDDED_H_ */

