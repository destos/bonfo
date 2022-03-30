"""Data classes that store parsed information from a MSP message."""

from dataclasses import dataclass, field
from typing import Optional

from dataclass_wizard import YAMLWizard


@dataclass
class Config:
    api_version: str = "0.0.0"
    flight_controller_identifier: str = ''
    flight_controller_version: str = ''
    version: int = 0
    build_info: str = ''
    multi_type: int = 0
    msp_version: int = 0
    capability: int = 0
    cycle_time: int = 0
    i2c_error: int = 0
    active_sensors: int = 0
    mode: int = 0
    profile: int = 0
    uid: list = field(default_factory=lambda: [0, 0, 0])
    accelerometer_trims: list = field(default_factory=lambda: [0, 0])
    name: str = ''
    display_name: str = 'pilot'
    num_profiles: int = 3
    rate_profile: int = 0
    board_type: int = 0
    arming_disable_count: int = 0
    arming_disable_flags: int = 0
    arming_disabled: bool = False
    runaway_takeoff_prevention_disabled: bool = False
    board_identifier: str = ""
    board_version: int = 0
    comm_capabilities: int = 0
    target_name: str = ""
    board_name: str = ""
    manufacturer_id: str = ""
    signature: list = field(default_factory=lambda: [])
    mcu_type_id: int = 255

    @property
    def is_inav(self):
        return "INAV" in self.flight_controller_identifier


# State and others  potentially can be an enum?
# Revamp how this is used in the FC msp client code and state + msp version switching
@dataclass
class DataHandler:
    msp_version: int = 1
    state: float = 0
    flags: int = 0
    message_direction: int = -1
    code: int = 0
    data_view: int = 0
    message_length_expected: int = 0
    message_length_received: int = 0
    message_buffer: list = field(default_factory=lambda: [])
    message_buffer_uint8_view: list = field(default_factory=lambda: [])
    message_checksum: int = 0
    messageIsJumboFrame: bool = False
    crcError: bool = False
    callbacks: list = field(default_factory=lambda: [])
    packet_error: int = 0
    unsupported: int = 0
    last_received_timestamp: Optional[float] = None
    listeners: list = field(default_factory=lambda: [])
    # TODO: state property with data class wizard that tracks field changes and logs them?


# @dataclass
# class SensorData:
#     gyroscope: int = [0, 0, 0]
#     accelerometer: int = [0, 0, 0]
#     magnetometer: int = [0, 0, 0]
#     altitude: int = 0
#     sonar: int = 0
#     kinematics: int = [0.0, 0.0, 0.0]
#     debug: int = [0, 0, 0, 0, 0, 0, 0, 0]  # 8 values for special situations like MSP2_INAV_DEBUG


# # @dataclass
# # class MotorData:
# #     # defaults
# #     # roll, pitch, yaw@dataclass, throttle, aux 1 ... aux n


# @dataclass
# class Rc:
#     active_channels: int = 0
#     channels: int = ([0] * 32,)


# @dataclass
# class GpsData:
#     fix: int = 0
#     numSat: int = 0
#     lat: int = 0
#     lon: int = 0
#     alt: int = 0
#     speed: int = 0
#     ground_course: int = 0
#     distanceToHome: int = 0
#     ditectionToHome: int = 0
#     update: int = 0
#     chn: int = []
#     svid: int = []
#     quality: int = []
#     cno: int = []


# # @dataclass
# # class Analog:
# # @dataclass
# # class Voltage_Meters:
# # @dataclass
# # class Current_Meters:
# # @dataclass
# # class Battery_State:


# @dataclass
# class Sensor_Alignment:
#     align_gyro: int = 0
#     align_acc: int = 0
#     align_mag: int = 0
#     gyro_detection_flags: int = 0
#     gyro_to_use: int = 0
#     gyro_1_align: int = 0
#     gyro_2_align: int = 0


# @dataclass
# class Board_Alignment_Config:
#     roll: int = 0
#     pitch: int = 0
#     yaw: int = 0


# @dataclass
# class Arming_Config:
#     auto_disarm_delay: int = 0
#     disarm_kill_switch: int = 0
#     small_angle: int = 0


# # @dataclass
# # class Feature_Config:
# #     featuremask: int =                    0

# #     features: int =                      {
# #             0: { 'group: int =  'rxMode', 'name: int =  'RX_PPM', 'enabled: int =  False
# #             2: { 'group: int =  'other', 'name: int =  'INFLIGHT_ACC_CAL', 'enabled: int =  False
# #             3: { 'group: int =  'rxMode', 'name: int =  'RX_SERIAL', 'enabled: int =  False
# #             4: { 'group: int =  'esc', 'name: int =  'MOTOR_STOP', 'enabled: int =  False
# #             5: { 'group: int =  'other', 'name: int =  'SERVO_TILT', 'enabled: int =  False
# #             6: { 'group: int =  'other', 'name: int =  'SOFTSERIAL', 'enabled: int =  False
# #             7: { 'group: int =  'gps', 'name: int =  'GPS', 'enabled: int =  False
# #             9: { 'group: int =  'other', 'name: int =  'SONAR', 'enabled: int =  False
# #             10: { 'group: int =  'other', 'name: int =  'TELEMETRY', 'enabled: int =  False
# #             12: { 'group: int =  '3D', 'name: int =  '3D', 'enabled: int =  False
# #             13: { 'group: int =  'rxMode', 'name: int =  'RX_PARALLEL_PWM', 'enabled: int =  False
# #             14: { 'group: int =  'rxMode', 'name: int =  'RX_MSP', 'enabled: int =  False
# #             15: { 'group: int =  'rssi', 'name: int =  'RSSI_ADC', 'enabled: int =  False
# #             16: { 'group: int =  'other', 'name: int =  'LED_STRIP', 'enabled: int =  False
# #             17: { 'group: int =  'other', 'name: int =  'DISPLAY', 'enabled: int =  False
# #             19: { 'group: int =  'other', 'name: int =  'BLACKBOX', 'enabled: int =  False
# #             20: { 'group: int =  'other', 'name: int =  'CHANNEL_FORWARDING', 'enabled: int =  False
# #             21: { 'group: int =  'other', 'name: int =  'TRANSPONDER', 'enabled: int =  False
# #             22: { 'group: int =  'other', 'name: int =  'AIRMODE', 'enabled: int =  False
# #             18: { 'group: int =  'other', 'name: int =  'OSD', 'enabled: int =  False
# #             25: { 'group: int =  'rxMode', 'name: int =  'RX_SPI', 'enabled: int =  False
# #             27: { 'group: int =  'other', 'name: int =  'ESC_SENSOR', 'enabled: int =  False
# #             28: { 'group: int =  'other', 'name: int =  'ANTI_GRAVITY', 'enabled: int =  False
# #             29: { 'group: int =  'other', 'name: int =  'DYNAMIC_FILTER', 'enabled: int =  False


@dataclass
class RxConfig:
    serialrx_provider: int = 0
    stick_max: int = 0
    stick_center: int = 0
    stick_min: int = 0
    spektrum_sat_bind: int = 0
    rx_min_usec: int = 0
    rx_max_usec: int = 0
    rc_interpolation: int = 0
    rc_interpolation_interval: int = 0
    rc_interpolation_channels: int = 0
    air_mode_activate_threshold: int = 0
    rx_spi_protocol: int = 0
    rx_spi_id: int = 0
    rx_spi_rf_channel_count: int = 0
    fpv_cam_angle_degrees: int = 0
    rc_smoothing_type: int = 0
    rc_smoothing_input_cutoff: int = 0
    rc_smoothing_derivative_cutoff: int = 0
    rc_smoothing_input_type: int = 0
    rc_smoothing_derivative_type: int = 0


# @dataclass
# class Profile(YAMLWizard):
#     rc_tuning: RcTuning = []


@dataclass
class RcTuning(YAMLWizard):
    # May allow for saving the raw byte value to get more percission than the float value conversion?
    # TODO: decimals in the future? store actual byte values and convert as needed?
    rc_rate: float = 0
    rc_expo: float = 0
    roll_pitch_rate: float = 0  # pre 1.7 api only
    roll_rate: float = 0
    pitch_rate: float = 0
    yaw_rate: float = 0
    dynamic_thr_pid: float = 0
    throttle_mid: float = 0
    throttle_expo: float = 0
    dynamic_thr_breakpoint: float = 0
    rc_yaw_expo: float = 0
    rcyawrate: float = 0
    rcpitchrate: float = 0
    rc_pitch_expo: float = 0
    roll_rate_limit: int = 1998
    pitch_rate_limit: int = 1998
    yaw_rate_limit: int = 1998

    def apply_struct(self, data):
        self.struct.parse(data)
        breakpoint()


# # @dataclass
# # class Rc_Map:

# # @dataclass
# # class Aux_Config_Ids:

# # @dataclass
# # class Mode_Ranges:

# # @dataclass
# # class Mode_Ranges_Extra:

# # @dataclass
# # class Adjustment_Ranges:

# # @dataclass
# # class Rxfail_Config:


# @dataclass
# class Failsafe_Config:
#     failsafe_delay: int = 0
#     failsafe_off_delay: int = 0
#     failsafe_throttle: int = 0
#     failsafe_switch_mode: int = 0
#     failsafe_throttle_low_delay: int = 0
#     failsafe_procedure: int = 0


# # @dataclass
# # class ServoData:

# # @dataclass
# # class Voltage_Meter_Configs:

# # @dataclass
# # class Current_Meter_Configs:

# @dataclass
# class Battery_Config:
#     vbatmincellvoltage: int = 0
#     vbatmaxcellvoltage: int = 0
#     vbatwarningcellvoltage: int = 0
#     capacity: int = 0
#     voltageMeterSource: int = 0
#     currentMeterSource: int = 0


# # @dataclass
# # class Pids:

# # @dataclass
# # class Pid:
# #     controller: int =                  0


# @dataclass
# class Fc_Config:
#     loopTime: int = 0


# @dataclass
# class Motor_Config:
#     minthrottle: int = 0
#     maxthrottle: int = 0
#     mincommand: int = 0


# @dataclass
# class Misc:
#     # DEPRECATED = only used to store values that are written back to the fc as-is, do NOT use for any other purpose
#     failsafe_throttle: int = 0
#     gps_baudrate: int = 0
#     multiwiicurrentoutput: int = 0
#     placeholder2: int = 0
#     vbatscale: int = 0
#     vbatmincellvoltage: int = 0
#     vbatmaxcellvoltage: int = 0
#     vbatwarningcellvoltage: int = 0
#     batterymetertype: int = 1  # 1=ADC, 2=ESC


# @dataclass
# class Gps_Config:
#     provider: int = 0
#     ublox_sbas: int = 0
#     auto_config: int = 0
#     auto_baud: int = 0


# @dataclass
# class Rssi_Config:
#     channel: int = 0


# @dataclass
# class Compass_Config:
#     mag_declination: int = 0


# @dataclass
# class Gps_Rescue:
#     angle: int = 0
#     initialAltitudeM: int = 0
#     descentDistanceM: int = 0
#     rescueGroundspeed: int = 0
#     throttleMin: int = 0
#     throttleMax: int = 0
#     throttleHover: int = 0
#     sanityChecks: int = 0
#     minSats: int = 0


# @dataclass
# class Motor_3d_Config:
#     deadband3d_low: int = 0
#     deadband3d_high: int = 0
#     neutral: int = 0


# # @dataclass
# # class Aux_Config:
# # @dataclass
# # class Pidnames:
# # @dataclass
# # class Servo_Config:


# @dataclass
# class Rc_Deadband_Config:
#     deadband: int = 0
#     yaw_deadband: int = 0
#     alt_hold_deadband: int = 0
#     deadband3d_throttle: int = 0


# @dataclass
# class Beeper_Config:
#     beepers: int = 0
#     dshotBeaconTone: int = 0
#     dshotBeaconConditions: int = 0


# @dataclass
# class Mixer_Config:
#     mixer: int = 0
#     reverseMotorDir: int = 0


# @dataclass
# class Reboot_Types:
#     FIRMWARE: int = 0
#     BOOTLOADER: int = 1
#     MSC: int = (2,)
#     MSC_UTC: int = 3


# # 0 based index, must be identical to 'baudRates' in 'src/main/io/serial.c' in betaflight
# # @dataclass
# # class Baud_Rates:
# # 230400', '250000', '400000', '460800', '500000', '921600', '1000000',
# # 1500000', '2000000', '2470000']

# # needs to be identical to 'serialPortFunction_e' in 'src/main/io/serial.h' in betaflight
# @dataclass
# class Serial_Port_Functions:
#     MSP: int = 0
#     GPS: int = 1
#     TELEMETRY_FRSKY: int = 2
#     TELEMETRY_HOTT: int = 3
#     TELEMETRY_MSP: int = 4
#     TELEMETRY_LTM: int = 4  # LTM replaced MSP
#     TELEMETRY_SMARTPORT: int = 5
#     RX_SERIAL: int = 6
#     BLACKBOX: int = 7
#     TELEMETRY_MAVLINK: int = 9
#     ESC_SENSOR: int = 1
#     TBS_SMARTAUDIO: int = 11
#     TELEMETRY_IBUS: int = 12
#     IRC_TRAMP: int = 13
#     RUNCAM_DEVICE_CONTROL: int = 14  # support communicate with RunCam Device
#     LIDAR_TF: int = 15


# @dataclass
# class Serial_Config:
#     ports: int = []
#     # pre 1.6 settings
#     mspBaudRate: int = 0
#     gpsBaudRate: int = 0
#     gpsPassthroughBaudRate: int = 0
#     cliBaudRate: int = 0


# @dataclass
# class Pid_Advanced_Config:
#     gyro_sync_denom: int = 0
#     pid_process_denom: int = 0
#     use_unsyncedPwm: int = 0
#     fast_pwm_protocol: int = 0
#     motor_pwm_rate: int = 0
#     digitalIdlePercent: int = 0
#     gyroUse32kHz: int = 0


# @dataclass
# class Filter_Config:
#     gyro_hardware_lpf: int = 0
#     gyro_32khz_hardware_lpf: int = 0
#     gyro_lowpass_hz: int = 0
#     gyro_lowpass_dyn_min_hz: int = 0
#     gyro_lowpass_dyn_max_hz: int = 0
#     gyro_lowpass_type: int = 0
#     gyro_lowpass2_hz: int = 0
#     gyro_lowpass2_type: int = 0
#     gyro_notch_hz: int = 0
#     gyro_notch_cutoff: int = 0
#     gyro_notch2_hz: int = 0
#     gyro_notch2_cutoff: int = 0
#     dterm_lowpass_hz: int = 0
#     dterm_lowpass_dyn_min_hz: int = 0
#     dterm_lowpass_dyn_max_hz: int = 0
#     dterm_lowpass_type: int = 0
#     dterm_lowpass2_hz: int = 0
#     dterm_lowpass2_type: int = 0
#     dterm_notch_hz: int = 0
#     dterm_notch_cutoff: int = 0
#     yaw_lowpass_hz: int = 0


# @dataclass
# class Advanced_Tuning:
#     rollPitchItermIgnoreRate: int = 0
#     yawItermIgnoreRate: int = 0
#     yaw_p_limit: int = 0
#     deltaMethod: int = 0
#     vbatPidCompensation: int = 0
#     dtermSetpointTransition: int = 0
#     dtermSetpointWeight: int = 0
#     toleranceBand: int = 0
#     toleranceBandReduction: int = 0
#     itermThrottleGain: int = 0
#     pidMaxVelocity: int = 0
#     pidMaxVelocityYaw: int = 0
#     levelAngleLimit: int = 0
#     levelSensitivity: int = 0
#     itermThrottleThreshold: int = 0
#     itermAcceleratorGain: int = 0
#     itermRotation: int = 0
#     smartFeedforward: int = 0
#     itermRelax: int = 0
#     itermRelaxType: int = 0
#     absoluteControlGain: int = 0
#     throttleBoost: int = 0
#     acroTrainerAngleLimit: int = 0
#     feedforwardRoll: int = 0
#     feedforwardPitch: int = 0
#     feedforwardYaw: int = 0
#     feedforwardTransition: int = 0
#     antiGravityMode: int = 0
#     dMinRoll: int = 0
#     dMinPitch: int = 0
#     dMinYaw: int = 0
#     dMinGain: int = 0
#     dMinAdvance: int = 0
#     useIntegratedYaw: int = 0
#     integratedYawRelax: int = 0


# @dataclass
# class Sensor_Config:
#     acc_hardware: int = 0
#     baro_hardware: int = 0
#     mag_hardware: int = 0


# @dataclass
# class Dataflash:
#     ready: bool = False
#     supported: bool = False
#     sectors: int = 0
#     totalSize: int = 0
#     usedSize: int = 0


# @dataclass
# class Sdcard:
#     supported: bool = False
#     state: int = 0
#     filesystemLastError: int = 0
#     freeSizeKB: int = 0
#     totalSizeKB: int = 0


# @dataclass
# class Blackbox:
#     supported: bool = False
#     blackboxDevice: int = 0
#     blackboxRateNum: int = 1
#     blackboxRateDenom: int = 1
#     blackboxPDenom: int = 0


# @dataclass
# class Transponder:
#     supported: bool = False
#     data: int = []
#     provider: int = 0
#     providers: int = []
