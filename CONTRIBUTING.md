# Contributing

Thanks for helping improve T2 Fan Control.

## Before opening an issue

Include the Ubuntu release, GNOME version, session type, T2FanRD version, and tiny-dfr version when relevant. Remove usernames, serial numbers, hardware identifiers, and unrelated journal output from logs.

Useful diagnostic commands:

```bash
lsb_release -ds
gnome-shell --version
printf 'Session: %s\n' "$XDG_SESSION_TYPE"
dpkg-query -W t2fanrd tiny-dfr 2>/dev/null
```

Describe the expected behavior and the exact steps that reproduce the issue. Screenshots are useful for dashboard or Touch Bar layout issues.

## Changes

- Keep privileged operations in `t2fantray-helper` and accept only explicit, fixed operations.
- Preserve existing user sections when updating `/etc/tiny-dfr/config.toml`.
- Do not restart tiny-dfr for ordinary fan mode or icon updates; its configuration is watched in place.
- Keep Battery and Time at the outside end of the Touch Bar row, with the optional fan immediately before Battery.
- Update both Vietnamese and English UI strings when adding visible text.
- Document installer/uninstaller behavior and any new system paths.

## Hardware verification

This app needs a T2 Mac and a GNOME desktop to verify real fan control, tray behavior, Polkit prompts, and Touch Bar input. When testing a change, record which parts were tested on hardware and which were only reviewed statically. Never test maximum fan mode without a way to return to Auto.
