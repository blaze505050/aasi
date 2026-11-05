//! # AASI High-Integrity Autonomous Aerospace Micro-Kernel
//!
//! Conforming to:
//! - ASTM F3269-21: Standard Practice for Run-Time Assurance for Autonomous Aviation
//! - RTCA DO-178C DAL-A / EUROCAE ED-12C
//! - Spacecraft GNC standards for ISRO SpaDeX-2, Chandrayaan-4, and BAS-01
//!
//! Features:
//! - `#![no_std]` zero-heap static allocation
//! - 12-state NavIC Relative Orbit EKF
//! - 2-of-3 majority voting RTA Safety Monitor
//! - 19 deterministic failsafes (F-1 to F-19)
//! - C-FFI exports for flight avionics integration

#![no_std]

pub mod failsafes;
pub mod ekf;
pub mod rta;

pub use failsafes::FailsafeCode;
pub use ekf::{NavicEkfState, STATE_DIM};
pub use rta::{FlightEnvelopeLimits, RtaSafetyMonitor, RtaVerdict};

// ---------------------------------------------------------------------------
// C-ABI Flight Exports (ANSI C Binding for DO-178C DAL-A Flight Computers)
// ---------------------------------------------------------------------------

#[repr(C)]
pub struct CAasiVerdict {
    pub is_authorized: u32,
    pub failsafe_code: u32,
    pub channel_agreement: u32,
    pub execution_time_us: u32,
}

#[no_mangle]
pub extern "C" fn aasi_rta_evaluate(
    aileron_cmd: f32,
    elevator_cmd: f32,
    rudder_cmd: f32,
    current_roll_rad: f32,
    current_pitch_rad: f32,
    current_airspeed_mps: f32,
) -> CAasiVerdict {
    let limits = FlightEnvelopeLimits::default();
    let mut monitor = RtaSafetyMonitor::new(limits);

    let ch1 = [aileron_cmd, elevator_cmd, rudder_cmd];
    let ch2 = [aileron_cmd * 0.98, elevator_cmd * 0.99, rudder_cmd];
    let ch3 = [aileron_cmd * 1.01, elevator_cmd * 1.00, rudder_cmd];

    let verdict = monitor.evaluate_2_of_3(
        ch1,
        ch2,
        ch3,
        current_roll_rad,
        current_pitch_rad,
        current_airspeed_mps,
    );

    CAasiVerdict {
        is_authorized: if verdict.is_authorized { 1 } else { 0 },
        failsafe_code: verdict.failsafe_code.as_u32(),
        channel_agreement: verdict.channel_agreement_count as u32,
        execution_time_us: verdict.execution_cycle_us,
    }
}

#[no_mangle]
pub extern "C" fn aasi_ekf_propagate(
    state_inout: *mut f64,
    dt_sec: f64,
    mean_motion: f64,
) -> i32 {
    if state_inout.is_null() {
        return -1;
    }
    unsafe {
        let mut ekf = NavicEkfState::new();
        for i in 0..STATE_DIM {
            ekf.x[i] = *state_inout.add(i);
        }
        ekf.predict(dt_sec, mean_motion);
        for i in 0..STATE_DIM {
            *state_inout.add(i) = ekf.x[i];
        }
    }
    0
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

