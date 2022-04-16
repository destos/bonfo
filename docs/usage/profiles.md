Betaflight gives you access to a few customization profiles when configuring your flight controller. This allows you to set specific PIDs and rate groups for different scenarios. For example, you could set a pid and rate profile aside for testing purposes, or separate your racing and freestyle rates/PIDs into different profiles.

Currently Betaflight allows for **3 PID profiles** and **6 rate profiles**.

# Scripting

If you're interested in interacting with your profiles programmatically, here are a few code examples that can help.

## Profile selection:

To manually select the rate or PID profile update the board's profile `pid` or `rate` attributes and run the profile's `apply_changes()` method asynchronously.

```python
async def manual_change_profile_coro():
    async with Board("/dev/tty0000").connect() as board:
        print(f"Before: {board.profile}")
        # > Before pid: 1 rate: 1
        board.profile.pid = 3
        board.profile.rate = 3
        print(f"After setting: {board.profile}")
        # After setting: pid: 1 rate: 1
        # note: profiles not applied to the board yet
        await board.profile.apply_changes()
        print(f"After: {board.profile}")
        # > After: pid: 2 rate: 2
```

To manage the profile with a context manager call the `profile` instance.

```python
async def change_profile_coro():
    async with Board("/dev/tty0000").connect() as board:
        print(f"Before: {board.profile}")
        # > Before: pid: 1 rate: 1
        async with board.profile(pid=2, rate=2) as profile:
            print(f"During: {board.profile}")
            # > During: pid: 2 rate: 2
            # Use board here with profile modifying or retrieval commands.
        # Using profile relevant commands outside the context manager scope should interact with the profiles set in our board.profile() call.
        print(f"After: {board.profile}")
        # > After: pid: 2 rate: 2
```

To set the board's pid and rate profile to their initial values after exiting the context manager, use the `revert_on_exit` kwarg set to `True`.

```python
async def change_profile_coro():
    async with Board("/dev/tty0000").connect() as board:
        print(f"Before: {board.profile}")
        # > pid: 1 rate: 1
        async with board.profile(pid=2, rate=2, revert_on_exit=True) as profile:
            print(f"During: {board.profile}")
            # > pid: 2 rate: 2
            # Use board here with profile modifying or retrieval commands.
        # Using profile relevant commands outside the context manager scope should interact with the profiles before our board.profile() call.
        print(f"After: {board.profile}")
        # > pid: 1 rate: 1
        # Profiles were reverted on context manager exit.
```
