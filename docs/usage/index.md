---
title: Bonfo usage
---

Bonfo can be used a few different ways to automate configuration and communication with your flight controllers.

There also is a [command line utility](./cli.md) provided that speeds up common user interactions and as an interface for applying previously saved configurations.

# As a module

``` python
# TODO: this doesn't work currently
import asyncio
from rich import print

from bonfo import Board
from bonfo.msp.fields import Name, Features, FeatureConfig, EepromWrite

async def main():
    async with Board("/dev/tty.usbmodem0x80000001").connect() as board:
        await (board < Name("slim shady"))
        name = await (board > Name)
        print(f"My name is what? {name}")
        # Get current enabled features...
        features_conf = await (board > FeatureConfig)
        print(features_conf)
        # Make sure we have serial RX enabled
        features_conf.features += Features.RX_SERIAL
        await (board < features_conf)
        # Save our changes
        await (board < EepromWrite())
        # Check that they made it
        features_conf = await (board > FeatureConfig)
        print(features_conf)

asyncio.run(main())
```
