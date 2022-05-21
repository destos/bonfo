The `Board` class is the main entrypoint to communicate with your connected flight controllers.

# Scripting

## Connecting manually

One option for communicating with the board is to wait for the ready event and then perform any desired board operations.

=== "script"
    ```python
    import asyncio
    from rich import print

    from bonfo import Board
    from bonfo.msp import StatusEx

    async def main():
        board = Board("/dev/tty.usbmodem0x80000001")
        await board.ready.wait()
        print(board.info)
        print(str(board.profile))
        _, data = await board.get(StatusEx)
        print(data)
        board.disconnect()

    asyncio.run(main())
    ```

=== "output"
    ```python
    CombinedBoardInfo(
        name=None,
        api=ApiVersion(msp_protocol=0, api_major=1, api_minor=43),
        version=FcVersion(major=4, minor=2, patch=11),
        build=BuildInfo(date_time=<Arrow [2021-11-09T20:27:49+00:00]>, git_hash='948ba63'),
        board=BoardInfo(
            short_name='S405',
            hardware_revision=0,
            uses_max7456=2,
            target_capabilities=<TargetCapabilitiesFlags.HAS_CUSTOM_DEFAULTS|SUPPORTS_CUSTOM_DEFAULTS|IS_UNIFIED|HAS_SOFTSERIAL|HAS_VCP: 55>,
            _target_name_length=9,
            target_name='STM32F405',
            _board_name_length=10,
            board_name='CLRACINGF4',
            _manufacturer_id_length=4,
            manufacturer_id='CLRA',
            signature='',
            mcu_type=3,
            configuration_state=2,
            sample_rate=16415,
            configuration_problems=<ConfigurationProblemsFlags.0: 0>
        ),
        variant=FcVariant(variant='BTFL'),
        uid=Uid(uid=ListContainer([520102400, 139540020, 926365744]))
    )
    pid: 1 rate: 5 SyncedState.CLEAN
    StatusEx(
        cycle_time=32000,
        i2c_error=0,
        active_sensors=<ActiveSensorsFlags.MAG|1: 33>,
        mode=0,
        pid_profile=1,
        cpuload=1280,
        profile_count=3,
        rate_profile=5,
        additional_mode_bytes=0,
        additional_mode=b'',
        arming_disable_flags=<ArmingDisableFlags.268435456|134217728|ARM_SWITCH|GPS: 436469760>,
        config_state=<ConfigStateFlags.0: 0>
    )
    ```

## Using the async context manager

Using the much shorter async manager `connect` is preferred.

``` python
import asyncio
from rich import print

from bonfo import Board
from bonfo.msp import StatusEx, SensorAlignment

async def main():
    async with Board("/dev/tty.usbmodem0x80000001").connect() as board:
        print(board.info)
        print(str(board.profile))
        _, data = await board.get(StatusEx)
        _, sensor = await board.get(SensorAlignment)
        print(data)
        print(sensor)

asyncio.run(main())
```

You should see the same output as the script above.
