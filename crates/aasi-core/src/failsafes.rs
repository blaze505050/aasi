//! Failsafe catalog conforming to ASTM F3269-21 and RTCA DO-178C DAL-A.
//! Implements deterministic violation codes F-1 through F-19 with zero heap allocation.

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
#[repr(u32)]
pub enum FailsafeCode {
    Nominal = 0,
    F1InvalidCognitiveStage = 1,
    F2InvalidEd25519Signature = 2,
    F3MissingMandatoryField = 3,
    F4MerkleProvenanceMismatch = 4,
    F5SafetyMonitorDisagreement = 5,
    F6HeartbeatLossTimeout = 6,
    F7RateOfClimbExceeded = 7,
    F8EnvelopeKinematicViolation = 8,
    F9AttitudeLimitExceeded = 9,
    F10DynamicPressureLimit = 10,
    F11GeofenceBoundaryBreached = 11,
    F12ActuatorSaturation = 12,
    F13NavicCovarianceDivergence = 13,
    F14EclipseGNSSOutage = 14,
    F15InterSatelliteLinkLost = 15,
    F16ThrusterPlumeContamination = 16,
    F17RelativeVelocityExcess = 17,
    F18ThermalExceedance = 18,
    F19BatteryDepthOfDischarge = 19,
}

impl FailsafeCode {
    pub const fn as_u32(self) -> u32 {
        self as u32
    }

    pub const fn is_emergency(self) -> bool {
        match self {
            Self::Nominal => false,
            Self::F5SafetyMonitorDisagreement
            | Self::F8EnvelopeKinematicViolation
            | Self::F11GeofenceBoundaryBreached
            | Self::F17RelativeVelocityExcess => true,
            _ => false,
        }
    }
}

