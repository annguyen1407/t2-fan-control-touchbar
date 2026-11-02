# Third-party sources and notices

T2 Fan Control is an integration app. The projects below remain separate dependencies; this repository does not vendor their source code.

| Project/source | How this project uses it | Upstream license / notes |
|---|---|---|
| [T2FanRD](https://github.com/GnomedDev/T2FanRD) | Runs the fan-control daemon; this app edits its `/etc/t2fand.conf` settings and restarts its service. | [GPL-3.0](https://github.com/GnomedDev/T2FanRD/blob/master/LICENCE). No T2FanRD source code is copied here. |
| [tiny-dfr](https://github.com/AsahiLinux/tiny-dfr) | Renders the configurable Touch Bar and receives its key actions. The optional updater builds [tag v0.3.7](https://github.com/AsahiLinux/tiny-dfr/tree/v0.3.7). | [MIT](https://github.com/AsahiLinux/tiny-dfr/blob/master/LICENSE). The build script downloads upstream source temporarily; it does not store it in this repository. |
| [T2Linux Wiki: Basic setup](https://wiki.t2linux.org/guides/postinstall/) | Reference for installing tiny-dfr and configuring `/etc/tiny-dfr/config.toml` on T2 Macs. | Documentation reference; no wiki text is bundled. |
| [GNOME Help: Set keyboard shortcuts](https://help.gnome.org/gnome-help/keyboard-shortcuts-set.html) | Reference for creating the GNOME shortcut that invokes the restricted helper. | Documentation reference; no GNOME documentation is bundled. |
| [GTK](https://www.gtk.org/) and [PyGObject](https://gitlab.gnome.org/GNOME/pygobject) | The GTK 3 UI toolkit and Python bindings used by the dashboard. | Installed as operating-system dependencies; their licenses and copyrights remain with upstream projects. |
| [Ayatana AppIndicator](https://github.com/AyatanaIndicators/libayatana-appindicator) | Provides the GTK 3 tray indicator API. | Upstream provides [LGPL-3.0](https://github.com/AyatanaIndicators/libayatana-appindicator/blob/main/COPYING). Installed as an operating-system dependency. |

## Artwork

`t2fantray.svg`, `fan-auto-white.svg`, and `fan-max-red.svg` are original artwork created for this repository. They are not copied or derived from tiny-dfr's Material Design icon assets. tiny-dfr's own upstream repository documents its icon asset licenses; those assets are not redistributed here.

## Independence

T2 Fan Control is an independent community project and is not affiliated with or endorsed by T2FanRD, AsahiLinux, T2Linux, GNOME, AyatanaIndicators, or Canonical/Ubuntu. Their names are used only to identify compatible projects and dependencies.
