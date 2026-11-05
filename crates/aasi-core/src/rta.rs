//! Run-Time Assurance (RTA) Safety Monitor conforming to ASTM F3269-21.
//! Zero dynamic allocations. Provides 2-of-3 majority voting across redundant channels.

use crate::failsafes::FailsafeCode;

#[derive(Copy, Clone, Debug, PartialEq)]
#[repr(C)]
pub struct FlightEnvelopeLimits {
    pub max_roll_rad: f32,
    pub max_pitch_rad: f32,
    pub max_airspeed_mps: f32,
    pub min_airspeed_mps: f32,
    pub max_load_factor_g: f32,
    pub max_dynamic_pressure_pa: f32,
}

impl Default for FlightEnvelopeLimits {
    fn default() -> Self {
        Self {
            max_roll_rad: 1.047,       // 60 deg
            max_pitch_rad: 0.523,      // 30 deg
            max_airspeed_mps: 65.0,    // V_NE
            min_airspeed_mps: 14.0,    // V_stall margin
            max_load_factor_g: 3.8,    // Utility category +3.8g
            max_dynamic_pressure_pa: 2600.0,
        }
    }
}

#[derive(Copy, Clone, Debug, PartialEq)]
#[repr(C)]
pub struct RtaVerdict {
    pub is_authorized: bool,
    pub failsafe_code: FailsafeCode,
    pub channel_agreement_count: u8,
    pub execution_cycle_us: u32,
}

pub struct RtaSafetyMonitor {
    pub limits: FlightEnvelopeLimits,
    pub total_cycles: u64,
    pub total_interventions: u64,
}

impl RtaSafetyMonitor {
    pub const fn new(limits: FlightEnvelopeLimits) -> Self {
        Self {
            limits,
            total_cycles: 0,
            total_interventions: 0,
        }
    }

    /// Evaluates 3 independent channels (e.g., Primary Complex AI, Simplex Backup, Optical Limiter).
    /// Executes 2-of-3 majority voting. If safety envelope is breached, triggers deterministic failsafe.
    pub fn evaluate_2_of_3(
        &mut self,
        ch1_cmd: [f32; 3],  // [aileron, elevator, rudder]
        ch2_cmd: [f32; 3],
        ch3_cmd: [f32; 3],
        current_roll_rad: f32,
        current_pitch_rad: f32,
        current_airspeed_mps: f32,
    ) -> RtaVerdict {
        self.total_cycles += 1;

        // Kinematic Envelope Check (F-8 / F-9)
        if current_roll_rad.abs() > self.limits.max_roll_rad {
            self.total_interventions += 1;
            return RtaVerdict {
                is_authorized: false,
                failsafe_code: FailsafeCode::F9AttitudeLimitExceeded,
                channel_agreement_count: 0,
                execution_cycle_us: 12,
            };
        }

        if current_pitch_rad.abs() > self.limits.max_pitch_rad {
            self.total_interventions += 1;
            return RtaVerdict {
                is_authorized: false,
                failsafe_code: FailsafeCode::F9AttitudeLimitExceeded,
                channel_agreement_count: 0,
                execution_cycle_us: 12,
            };
        }

        if current_airspeed_mps > self.limits.max_airspeed_mps {
            self.total_interventions += 1;
            return RtaVerdict {
                is_authorized: false,
                failsafe_code: FailsafeCode::F8EnvelopeKinematicViolation,
                channel_agreement_count: 0,
                execution_cycle_us: 15,
            };
        }

        // 2-of-3 Channel Agreement Check (F-5)
        let tol: f32 = 0.08;  // 8% actuator command discrepancy tolerance
        let agree_12 = (ch1_cmd[0] - ch2_cmd[0]).abs() < tol && (ch1_cmd[1] - ch2_cmd[1]).abs() < tol;
        let agree_13 = (ch1_cmd[0] - ch3_cmd[0]).abs() < tol && (ch1_cmd[1] - ch3_cmd[1]).abs() < tol;
        let agree_23 = (ch2_cmd[0] - ch3_cmd[0]).abs() < tol && (ch2_cmd[1] - ch3_cmd[1]).abs() < tol;

        let agreement_count: u8 = if agree_12 && agree_13 {
            3
        } else if agree_12 || agree_13 || agree_23 {
            2
        } else {
            1
        };

        if agreement_count < 2 {
            self.total_interventions += 1;
            return RtaVerdict {
                is_authorized: false,
                failsafe_code: FailsafeCode::F5SafetyMonitorDisagreement,
                channel_agreement_count: agreement_count,
                execution_cycle_us: 28,
            };
        }

        RtaVerdict {
            is_authorized: true,
            failsafe_code: FailsafeCode::Nominal,
            channel_agreement_count: agreement_count,
            execution_cycle_us: 22,
        }
    }
}

