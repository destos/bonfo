from enum import IntEnum


class MSP(IntEnum):
    API_VERSION = 1
    FC_VARIANT = 2
    FC_VERSION = 3
    BOARD_INFO = 4
    BUILD_INFO = 5

    NAME = 10
    SET_NAME = 11

    BATTERY_CONFIG = 32
    SET_BATTERY_CONFIG = 33
    MODE_RANGES = 34
    SET_MODE_RANGE = 35
    FEATURE_CONFIG = 36
    SET_FEATURE_CONFIG = 37
    BOARD_ALIGNMENT_CONFIG = 38
    SET_BOARD_ALIGNMENT_CONFIG = 39
    CURRENT_METER_CONFIG = 40
    SET_CURRENT_METER_CONFIG = 41
    MIXER_CONFIG = 42
    SET_MIXER_CONFIG = 43
    RX_CONFIG = 44
    SET_RX_CONFIG = 45
    LED_COLORS = 46
    SET_LED_COLORS = 47
    LED_STRIP_CONFIG = 48
    SET_LED_STRIP_CONFIG = 49
    RSSI_CONFIG = 50
    SET_RSSI_CONFIG = 51
    ADJUSTMENT_RANGES = 52
    SET_ADJUSTMENT_RANGE = 53
    CF_SERIAL_CONFIG = 54
    SET_CF_SERIAL_CONFIG = 55
    VOLTAGE_METER_CONFIG = 56
    SET_VOLTAGE_METER_CONFIG = 57
    SONAR = 58
    PID_CONTROLLER = 59
    SET_PID_CONTROLLER = 60
    ARMING_CONFIG = 61
    SET_ARMING_CONFIG = 62
    RX_MAP = 64
    SET_RX_MAP = 65
    BF_CONFIG = 66  # deprecated
    SET_BF_CONFIG = 67  # deprecated
    SET_REBOOT = 68
    BF_BUILD_INFO = 69  # deprecated
    DATAFLASH_SUMMARY = 70
    DATAFLASH_READ = 71
    DATAFLASH_ERASE = 72
    LOOP_TIME = 73
    SET_LOOP_TIME = 74
    FAILSAFE_CONFIG = 75
    SET_FAILSAFE_CONFIG = 76
    RXFAIL_CONFIG = 77
    SET_RXFAIL_CONFIG = 78
    SDCARD_SUMMARY = 79
    BLACKBOX_CONFIG = 80
    SET_BLACKBOX_CONFIG = 81
    TRANSPONDER_CONFIG = 82
    SET_TRANSPONDER_CONFIG = 83
    OSD_CONFIG = 84
    SET_OSD_CONFIG = 85
    OSD_CHAR_READ = 86
    OSD_CHAR_WRITE = 87
    VTX_CONFIG = 88
    SET_VTX_CONFIG = 89
    ADVANCED_CONFIG = 90
    SET_ADVANCED_CONFIG = 91
    FILTER_CONFIG = 92
    SET_FILTER_CONFIG = 93
    PID_ADVANCED = 94
    SET_PID_ADVANCED = 95
    SENSOR_CONFIG = 96
    SET_SENSOR_CONFIG = 97
    SPECIAL_PARAMETERS = 98  # deprecated
    ARMING_DISABLE = 99
    SET_SPECIAL_PARAMETERS = 99  # deprecated
    IDENT = 100  # deprecated
    STATUS = 101
    RAW_IMU = 102
    SERVO = 103
    MOTOR = 104
    RC = 105
    RAW_GPS = 106
    COMP_GPS = 107
    ATTITUDE = 108
    ALTITUDE = 109
    ANALOG = 110
    RC_TUNING = 111
    PID = 112
    BOX = 113  # deprecatedD
    MISC = 114  # deprecated
    BOXNAMES = 116
    PIDNAMES = 117
    WP = 118  # deprecated
    BOXIDS = 119
    SERVO_CONFIGURATIONS = 120
    MOTOR_3D_CONFIG = 124
    RC_DEADBAND = 125
    SENSOR_ALIGNMENT = 126
    LED_STRIP_MODECOLOR = 127

    VOLTAGE_METERS = 128
    CURRENT_METERS = 129
    BATTERY_STATE = 130
    MOTOR_CONFIG = 131
    GPS_CONFIG = 132
    COMPASS_CONFIG = 133
    GPS_RESCUE = 135

    STATUS_EX = 150

    UID = 160
    GPS_SV_INFO = 164

    GPSSTATISTICS = 166

    DISPLAYPORT = 182

    COPY_PROFILE = 183

    BEEPER_CONFIG = 184
    SET_BEEPER_CONFIG = 185

    SET_RAW_RC = 200
    SET_RAW_GPS = 201  # deprecated
    SET_PID = 202
    SET_BOX = 203  # deprecated
    SET_RC_TUNING = 204
    ACC_CALIBRATION = 205
    MAG_CALIBRATION = 206
    SET_MISC = 207  # deprecated
    RESET_CONF = 208
    SET_WP = 209  # deprecated
    SELECT_SETTING = 210
    SET_HEADING = 211  # deprecated
    SET_SERVO_CONFIGURATION = 212
    SET_MOTOR = 214
    SET_MOTOR_3D_CONFIG = 217
    SET_RC_DEADBAND = 218
    SET_RESET_CURR_PID = 219
    SET_SENSOR_ALIGNMENT = 220
    SET_LED_STRIP_MODECOLOR = 221
    SET_MOTOR_CONFIG = 222
    SET_GPS_CONFIG = 223
    SET_COMPASS_CONFIG = 224
    SET_GPS_RESCUE = 225
    # SET_CHANNEL_FORWARDING =  # TODO: find

    MODE_RANGES_EXTRA = 238
    SET_ACC_TRIM = 239
    ACC_TRIM = 240
    SERVO_MIX_RULES = 241
    SET_SERVO_MIX_RULE = 242  # deprecated
    SET_4WAY_IF = 245  # deprecated
    SET_RTC = 246
    RTC = 247  # deprecated
    SET_BOARD_INFO = 248  # deprecated
    SET_SIGNATURE = 249  # deprecated

    EEPROM_WRITE = 250
    DEBUGMSG = 253  # deprecated
    DEBUG = 254

    # INAV/v2 specific codes
    SETTING = 0x1003
    SET_SETTING = 0x1004

    COMMON_MOTOR_MIXER = 0x1005
    COMMON_SET_MOTOR_MIXER = 0x1006

    COMMON_SETTING_INFO = 0x1007
    COMMON_PG_LIST = 0x1008

    INAV_CF_SERIAL_CONFIG = 0x1009
    INAV_SET_CF_SERIAL_CONFIG = 0x100A

    INAV_STATUS = 0x2000
    INAV_OPTICAL_FLOW = 0x2001
    INAV_ANALOG = 0x2002
    INAV_MISC = 0x2003
    INAV_SET_MISC = 0x2004
    INAV_BATTERY_CONFIG = 0x2005
    INAV_SET_BATTERY_CONFIG = 0x2006
    INAV_RATE_PROFILE = 0x2007
    INAV_SET_RATE_PROFILE = 0x2008
    INAV_AIR_SPEED = 0x2009
    INAV_OUTPUT_MAPPING = 0x200A

    INAV_MIXER = 0x2010
    INAV_SET_MIXER = 0x2011

    INAV_OSD_LAYOUTS = 0x2012
    INAV_OSD_SET_LAYOUT_ITEM = 0x2013
    INAV_OSD_ALARMS = 0x2014
    INAV_OSD_SET_ALARMS = 0x2015
    INAV_OSD_PREFERENCES = 0x2016
    INAV_OSD_SET_PREFERENCES = 0x2017

    INAV_MC_BRAKING = 0x200B
    INAV_SET_MC_BRAKING = 0x200C

    INAV_SELECT_BATTERY_PROFILE = 0x2018

    INAV_DEBUG = 0x2019

    INAV_BLACKBOX_CONFIG = 0x201A
    INAV_SET_BLACKBOX_CONFIG = 0x201B

    INAV_SENSOR_CONFIG = 0x201C
    INAV_SET_SENSOR_CONFIG = 0x201D
    INAV_TEMPERATURES = 0x201E

    INAV_SERVO_MIXER = 0x2020
    INAV_SET_SERVO_MIXER = 0x2021
    INAV_LOGIC_CONDITIONS = 0x2022
    INAV_SET_LOGIC_CONDITIONS = 0x2023
    INAV_LOGIC_CONDITIONS_STATUS = 0x2026

    INAV_PID = 0x2030
    INAV_SET_PID = 0x2031

    INAV_OPFLOW_CALIBRATION = 0x203
frame_map = {v.real: v for v in MSP.__members__.values()}
