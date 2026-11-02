# Troubleshooting

Run commands from a terminal in the same logged-in desktop session unless a command uses `sudo`.

## App icon does not appear

Check the required packages and launch the app from a terminal to see Python/GTK errors:

```bash
dpkg-query -W python3-gi gir1.2-ayatanaappindicator3-0.1
/usr/local/lib/t2fantray/t2fantray.py
```

The tray indicator may also depend on Ubuntu's AppIndicator support in GNOME. Confirm that the application is still running:

```bash
pgrep -af '/usr/local/lib/t2fantray/t2fantray.py'
```

## Fan mode does not change

Check T2FanRD and its recent logs:

```bash
sudo systemctl status t2fanrd.service --no-pager
sudo journalctl -u t2fanrd.service -b -n 80 --no-pager
```

Try the installed helper directly:

```bash
pkexec /usr/local/libexec/t2fantray-helper max
grep -E 'always_full_speed' /etc/t2fand.conf
```

For Auto, substitute `auto`. The helper restarts `t2fanrd.service` to apply the changed configuration. Check that the account's Polkit policy is installed at `/usr/share/polkit-1/actions/org.t2fantray.policy` if a graphical authentication prompt does not appear.

## GNOME shortcut or Touch Bar button does not toggle the mode

The GNOME custom shortcut should be created through **Settings → Keyboard → Custom Shortcuts**. Check that the entry has:

- Command: `pkexec /usr/local/libexec/t2fantray-helper toggle`
- Shortcut: `Ctrl+Shift+F11`

The Touch Bar button sends the same key chord. To test GNOME independently of the helper, create a temporary custom shortcut with `notify-send "Shortcut works"` as its command. If the notification appears, GNOME received the shortcut. Replace the test command with the helper command afterwards.

## Touch Bar button is missing or remains at the old position

Check that tiny-dfr is installed and running, and that the user configuration has a `MediaLayerKeys` array:

```bash
tiny-dfr --version
sudo systemctl status tiny-dfr.service --no-pager
sudo grep -nE 'MediaLayerKeys|fan_auto_white|fan_max_red|Battery|Time' /etc/tiny-dfr/config.toml
```

The app inserts its optional fan entry before Battery. Keep Battery and Time as the last entries if editing the list manually. The Touch Bar preference in the app must be enabled and T2 Fan Control must be running in the tray.

On tiny-dfr 0.3.7, config changes are watched in place. If the daemon is stopped or the config is invalid, inspect:

```bash
sudo journalctl -u tiny-dfr.service -b -n 80 --no-pager
```

## Verify login startup

The app's Settings page controls the user autostart entry:

```bash
ls -l ~/.config/autostart/t2fantray.desktop
pgrep -af '/usr/local/lib/t2fantray/t2fantray.py'
```

The first command checks whether autostart is enabled; the second checks whether the app is running in the current session.

## Remove stale manual GNOME shortcuts

If you created older T2 Fan Auto/Max shortcuts while troubleshooting, remove those entries in **Settings → Keyboard → Custom Shortcuts**. Keep one `T2 Fan Toggle` shortcut with the command and key chord above.
