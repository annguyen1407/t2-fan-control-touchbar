#!/usr/bin/env python3
"""Compact bilingual tray front end for T2FanRD."""

import configparser
import glob
import json
import os
import subprocess
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, Gdk, GLib, Gtk


CONFIG = "/etc/t2fand.conf"
HELPER = "/usr/local/libexec/t2fantray-helper"
PREFS = os.path.expanduser("~/.config/t2fantray/preferences.json")
AUTOSTART = os.path.expanduser("~/.config/autostart/t2fantray.desktop")
TOUCHBAR_CONFIG = "/etc/tiny-dfr/config.toml"
TOUCHBAR_BACKLIGHT_NAMES = ("display-pipe", "228600000.dsi.0", "appletb_backlight")

TEXT = {
    "vi": {
        "title": "T2 Fan Control",
        "automatic": "Tự động",
        "maximum": "Tối đa",
        "empty": "Không tìm thấy cảm biến quạt",
        "updating": "Đang cập nhật…",
        "updated": "Đã cập nhật",
        "failed": "Không áp dụng được chế độ quạt",
        "open": "Mở T2 Fan Control",
        "set_max": "Chạy quạt tối đa",
        "set_auto": "Trở về tự động",
        "quit": "Thoát",
        "fan": "Quạt",
        "service": "Điều khiển bởi T2FanRD",
        "notice_max": "Tốc độ tối đa đang bật",
        "notice_auto": "Đang theo đường cong tự động",
        "settings": "Cài đặt",
        "back": "Quay lại",
        "language": "Ngôn ngữ",
        "touchbar_setting": "Nút quạt Touch Bar",
        "touchbar_hint": "Hiện khi ứng dụng chạy ở khay",
        "autostart_setting": "Khởi động cùng Ubuntu",
        "autostart_hint": "Tự chạy sau khi đăng nhập",
        "mode_max_short": "Quạt đang chạy tối đa",
        "mode_auto_short": "Quạt đang ở chế độ tự động",
    },
    "en": {
        "title": "T2 Fan Control",
        "automatic": "Auto",
        "maximum": "Max",
        "empty": "No fan sensors found",
        "updating": "Applying…",
        "updated": "Updated",
        "failed": "Could not apply fan mode",
        "open": "Open T2 Fan Control",
        "set_max": "Set maximum speed",
        "set_auto": "Return to automatic",
        "quit": "Quit",
        "fan": "Fan",
        "service": "Managed by T2FanRD",
        "notice_max": "Maximum speed is on",
        "notice_auto": "Following automatic curve",
        "settings": "Settings",
        "back": "Back",
        "language": "Language",
        "touchbar_setting": "Touch Bar fan button",
        "touchbar_hint": "Show while the app runs in the tray",
        "autostart_setting": "Start with Ubuntu",
        "autostart_hint": "Launch after you sign in",
        "mode_max_short": "Fans are running at maximum",
        "mode_auto_short": "Fans are following the automatic curve",
    },
}


def load_preferences():
    try:
        with open(PREFS, encoding="utf-8") as f:
            values = json.load(f)
        if not isinstance(values, dict):
            values = {}
    except (OSError, ValueError, TypeError):
        values = {}
    if values.get("language") not in TEXT:
        values["language"] = "vi"
    values.setdefault("touchbar_enabled", True)
    return values


def save_preference(key, value):
    os.makedirs(os.path.dirname(PREFS), exist_ok=True)
    values = load_preferences()
    values[key] = value
    temp = PREFS + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(values, f)
    os.replace(temp, PREFS)


def read_full_speed():
    cfg = configparser.ConfigParser()
    try:
        cfg.read(CONFIG)
        sections = [s for s in cfg.sections() if s.lower().startswith("fan")]
        return bool(sections) and all(
            cfg.getboolean(section, "always_full_speed", fallback=False)
            for section in sections
        )
    except (OSError, configparser.Error, ValueError):
        return False


def fan_readings():
    readings = []
    for name_file in glob.glob("/sys/class/hwmon/hwmon*/name"):
        try:
            with open(name_file, encoding="utf-8") as f:
                if f.read().strip() != "macsmc_hwmon":
                    continue
            hwmon = os.path.dirname(name_file)
            for input_file in sorted(glob.glob(os.path.join(hwmon, "fan*_input"))):
                fan = os.path.basename(input_file).removesuffix("_input")
                try:
                    with open(input_file, encoding="utf-8") as f:
                        rpm = int(f.read().strip())
                    with open(os.path.join(hwmon, fan + "_max"), encoding="utf-8") as f:
                        maximum = int(f.read().strip())
                    readings.append((fan, rpm, maximum))
                except (OSError, ValueError):
                    continue
        except OSError:
            continue
    return readings


def touchbar_available():
    """Show Touch Bar controls only when its backlight and tiny-dfr config exist."""
    try:
        backlights = os.listdir("/sys/class/backlight")
    except OSError:
        return False
    has_touchbar = any(
        marker in name
        for name in backlights
        for marker in TOUCHBAR_BACKLIGHT_NAMES
    )
    return has_touchbar and os.path.isfile(TOUCHBAR_CONFIG)


class T2FanTray:
    def __init__(self):
        self.preferences = load_preferences()
        self.language = self.preferences["language"]
        self.touchbar_enabled = bool(self.preferences["touchbar_enabled"])
        self.touchbar_available = touchbar_available()
        self.autostart_enabled = os.path.isfile(AUTOSTART)
        self.applying = False
        self.current_full_speed = None
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "t2fantray", "t2fantray-auto", AyatanaAppIndicator3.IndicatorCategory.HARDWARE
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

        self.window = Gtk.Window(title=TEXT[self.language]["title"])
        self.window.set_default_size(336, 248)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self.hide_window)
        self.build_window()
        self.build_menu()
        self.translate()
        self.refresh()
        # The tray app is the feature's enabled state. Keep its Touch Bar
        # controls available while the app runs, even when its window is hidden.
        if self.touchbar_available:
            self.sync_touchbar_buttons(self.touchbar_enabled)
        GLib.timeout_add_seconds(2, self.refresh)

    def build_window(self):
        screen = Gdk.Screen.get_default()
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window.t2fan-window { background: #171a20; color: #f4f5f7; }
            .t2-page { background: #171a20; }
            .t2-title { color: #f5f6f8; font-size: 16px; font-weight: 700; }
            .t2-subtitle { color: #929aa7; font-size: 10px; }
            .t2-card { background: #222731; border: 1px solid #2c333f; border-radius: 12px; padding: 9px 11px; }
            .t2-fan-name { color: #e7eaf0; font-size: 11px; font-weight: 600; }
            .t2-rpm { color: #c6ccd5; font-size: 11px; font-weight: 600; }
            .t2-mode button { background: #222731; color: #bdc4cf; border: 1px solid #303744; border-radius: 8px; padding: 7px 12px; }
            .t2-mode button.selected { background: #2b5ca8; color: white; border-color: #3e78d0; }
            .t2-mode button.max-selected { background: #8f302e; color: white; border-color: #bb403a; }
            .t2-icon-button { background: transparent; border: 0; color: #aab2bf; padding: 5px; }
            .t2-setting-title { color: #f0f2f5; font-size: 12px; font-weight: 600; }
            .t2-setting-hint { color: #929aa7; font-size: 10px; }
            .t2-setting-row { background: #222731; border: 1px solid #2c333f; border-radius: 10px; padding: 9px 10px; }
            .t2-status { color: #b8c0cc; font-size: 10px; }
            progressbar trough { min-height: 4px; background: #343b47; border-radius: 4px; }
            progressbar progress { min-height: 4px; background: #63a6ff; border-radius: 4px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.window.get_style_context().add_class("t2fan-window")

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(140)
        self.window.add(self.stack)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(14)
        page.get_style_context().add_class("t2-page")
        self.stack.add_named(page, "dashboard")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self.title_label = Gtk.Label(xalign=0)
        self.title_label.get_style_context().add_class("t2-title")
        self.subtitle_label = Gtk.Label(xalign=0)
        self.subtitle_label.get_style_context().add_class("t2-subtitle")
        titles.pack_start(self.title_label, False, False, 0)
        titles.pack_start(self.subtitle_label, False, False, 0)
        top.pack_start(titles, True, True, 0)
        self.settings_button = Gtk.Button.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        self.settings_button.get_style_context().add_class("t2-icon-button")
        self.settings_button.connect("clicked", lambda *_: self.show_settings())
        top.pack_end(self.settings_button, False, False, 0)
        page.pack_start(top, False, False, 0)

        self.fan_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        page.pack_start(self.fan_box, True, True, 0)

        self.auto_button = Gtk.Button()
        self.max_button = Gtk.Button()
        modes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        modes.get_style_context().add_class("t2-mode")
        modes.pack_start(self.auto_button, True, True, 0)
        modes.pack_start(self.max_button, True, True, 0)
        self.auto_button.connect("clicked", lambda *_: self.set_mode(False))
        self.max_button.connect("clicked", lambda *_: self.set_mode(True))
        page.pack_start(modes, False, False, 0)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.get_style_context().add_class("t2-status")
        page.pack_start(self.status_label, False, False, 0)

        settings_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_page.set_border_width(14)
        settings_page.get_style_context().add_class("t2-page")
        self.stack.add_named(settings_page, "settings")
        settings_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.back_button.get_style_context().add_class("t2-icon-button")
        self.back_button.connect("clicked", lambda *_: self.show_dashboard())
        settings_header.pack_start(self.back_button, False, False, 0)
        self.settings_title = Gtk.Label(xalign=0)
        self.settings_title.get_style_context().add_class("t2-title")
        settings_header.pack_start(self.settings_title, True, True, 0)
        settings_page.pack_start(settings_header, False, False, 0)

        language_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        language_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.language_label = Gtk.Label(xalign=0)
        self.language_label.get_style_context().add_class("t2-setting-title")
        language_labels.pack_start(self.language_label, False, False, 0)
        language_row.pack_start(language_labels, True, True, 0)
        self.language_combo = Gtk.ComboBoxText()
        self.language_combo.append("vi", "VI")
        self.language_combo.append("en", "EN")
        self.language_combo.set_active_id(self.language)
        self.language_combo.connect("changed", self.on_language_changed)
        language_row.pack_end(self.language_combo, False, False, 0)
        language_row.get_style_context().add_class("t2-setting-row")
        settings_page.pack_start(language_row, False, False, 0)

        self.autostart_switch = Gtk.Switch()
        if self.touchbar_available:
            self.touchbar_switch = Gtk.Switch()
            settings_page.pack_start(
                self.setting_row("touchbar_setting", "touchbar_hint", self.touchbar_switch), False, False, 0
            )
        settings_page.pack_start(
            self.setting_row("autostart_setting", "autostart_hint", self.autostart_switch), False, False, 0
        )
        if self.touchbar_available:
            self.touchbar_switch.set_active(self.touchbar_enabled)
            self.touchbar_switch.connect("notify::active", self.on_touchbar_setting)
        self.autostart_switch.set_active(self.autostart_enabled)
        self.autostart_switch.connect("notify::active", self.on_autostart_setting)
        self.stack.set_visible_child_name("dashboard")

    def setting_row(self, title_key, hint_key, switch):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(xalign=0)
        title.get_style_context().add_class("t2-setting-title")
        hint = Gtk.Label(xalign=0)
        hint.get_style_context().add_class("t2-setting-hint")
        setattr(self, f"{title_key}_label", title)
        setattr(self, f"{hint_key}_label", hint)
        labels.pack_start(title, False, False, 0)
        labels.pack_start(hint, False, False, 0)
        row.pack_start(labels, True, True, 0)
        row.pack_end(switch, False, False, 0)
        row.get_style_context().add_class("t2-setting-row")
        return row

    def build_menu(self):
        self.menu = Gtk.Menu()
        self.menu_open = Gtk.MenuItem()
        self.menu_open.connect("activate", lambda *_: self.show_window())
        self.menu.append(self.menu_open)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu_auto = Gtk.MenuItem()
        self.menu_auto.connect("activate", lambda *_: self.set_mode(False))
        self.menu.append(self.menu_auto)
        self.menu_max = Gtk.MenuItem()
        self.menu_max.connect("activate", lambda *_: self.set_mode(True))
        self.menu.append(self.menu_max)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu_quit = Gtk.MenuItem()
        self.menu_quit.connect("activate", lambda *_: self.quit_app())
        self.menu.append(self.menu_quit)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def translate(self):
        t = TEXT[self.language]
        self.window.set_title(t["title"])
        self.title_label.set_text(t["title"])
        self.subtitle_label.set_text(t["service"])
        self.auto_button.set_label(t["automatic"])
        self.max_button.set_label(t["maximum"])
        self.menu_auto.set_label(t["automatic"])
        self.menu_max.set_label(t["maximum"])
        self.menu_open.set_label(t["open"])
        self.menu_quit.set_label(t["quit"])
        self.settings_title.set_text(t["settings"])
        self.language_label.set_text(t["language"])
        if self.touchbar_available:
            self.touchbar_setting_label.set_text(t["touchbar_setting"])
            self.touchbar_hint_label.set_text(t["touchbar_hint"])
        self.autostart_setting_label.set_text(t["autostart_setting"])
        self.autostart_hint_label.set_text(t["autostart_hint"])
        self.indicator.set_title(t["title"])
        self.language_combo.set_tooltip_text("Language / Ngôn ngữ")
        self.settings_button.set_tooltip_text(t["settings"])
        self.back_button.set_tooltip_text(t["back"])
        self.refresh()

    def on_language_changed(self, combo):
        language = combo.get_active_id()
        if language in TEXT and language != self.language:
            self.language = language
            save_preference("language", language)
            self.translate()

    def show_settings(self):
        self.stack.set_visible_child_name("settings")
        self.window.resize(336, 230)

    def show_dashboard(self):
        self.stack.set_visible_child_name("dashboard")
        self.window.resize(336, 248)

    def on_touchbar_setting(self, switch, _param):
        if not self.touchbar_available:
            return
        enabled = switch.get_active()
        if enabled == self.touchbar_enabled:
            return
        self.touchbar_enabled = enabled
        save_preference("touchbar_enabled", enabled)
        self.sync_touchbar_buttons(enabled)

    def on_autostart_setting(self, switch, _param):
        enabled = switch.get_active()
        if enabled == self.autostart_enabled:
            return
        try:
            if enabled:
                os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
                with open(AUTOSTART, "w", encoding="utf-8") as f:
                    f.write(
                        "[Desktop Entry]\n"
                        "Type=Application\n"
                        "Name=T2 Fan Control\n"
                        "Comment=Fan control for T2 Macs\n"
                        "Exec=/usr/local/lib/t2fantray/t2fantray.py\n"
                        "Icon=t2fantray\n"
                        "Terminal=false\n"
                        "X-GNOME-Autostart-enabled=true\n"
                    )
            elif os.path.exists(AUTOSTART):
                os.unlink(AUTOSTART)
            self.autostart_enabled = enabled
            save_preference("autostart_enabled", enabled)
        except OSError as exc:
            switch.set_active(not enabled)
            self.status_label.set_text(str(exc))

    def hide_window(self, *_):
        self.window.hide()
        return True

    def show_window(self):
        self.refresh()
        self.window.show_all()
        self.window.present()

    def quit_app(self):
        if self.touchbar_available:
            try:
                subprocess.run(
                    ["pkexec", HELPER, "touchbar-hide"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
        Gtk.main_quit()

    def sync_touchbar_buttons(self, visible):
        if not self.touchbar_available:
            return
        operation = "touchbar-show" if visible else "touchbar-hide"
        threading.Thread(
            target=self._sync_touchbar_buttons,
            args=(operation,),
            daemon=True,
        ).start()

    def _sync_touchbar_buttons(self, operation):
        try:
            result = subprocess.run(
                ["pkexec", HELPER, operation],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            ok = result.returncode == 0
            message = result.stderr.strip() or result.stdout.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            ok = False
            message = str(exc)
        if not ok and operation == "touchbar-show":
            GLib.idle_add(self.status_label.set_text, message or TEXT[self.language]["failed"])

    def refresh(self, *_):
        readings = fan_readings()
        for child in self.fan_box.get_children():
            self.fan_box.remove(child)
        t = TEXT[self.language]
        if readings:
            for index, (_fan, rpm, maximum) in enumerate(readings, start=1):
                card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                card.get_style_context().add_class("t2-card")
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                name = Gtk.Label(label=f"{t['fan']} {index}", xalign=0)
                name.get_style_context().add_class("t2-fan-name")
                percent = round(100 * rpm / maximum) if maximum else 0
                value = Gtk.Label(label=f"{rpm:,} RPM  ·  {percent}%", xalign=1)
                value.get_style_context().add_class("t2-rpm")
                row.pack_start(name, True, True, 0)
                row.pack_end(value, False, False, 0)
                progress = Gtk.ProgressBar()
                progress.set_fraction(min(1.0, rpm / maximum) if maximum else 0.0)
                card.pack_start(row, False, False, 0)
                card.pack_start(progress, False, False, 0)
                self.fan_box.pack_start(card, False, False, 0)
        else:
            empty = Gtk.Label(label=t["empty"], xalign=0)
            empty.get_style_context().add_class("t2-subtitle")
            self.fan_box.pack_start(empty, False, False, 4)
        self.fan_box.show_all()

        full = read_full_speed()
        if full != self.current_full_speed:
            self.indicator.set_icon_full(
                "t2fantray-max" if full else "t2fantray-auto",
                t["notice_max"] if full else t["notice_auto"],
            )
            self.current_full_speed = full
        if not self.applying:
            for button, selected in ((self.max_button, full), (self.auto_button, not full)):
                context = button.get_style_context()
                context.remove_class("selected")
                context.remove_class("max-selected")
                if selected:
                    context.add_class("max-selected" if button is self.max_button else "selected")
            self.menu_max.set_label(("✓  " if full else "   ") + t["maximum"])
            self.menu_auto.set_label(("✓  " if not full else "   ") + t["automatic"])
            self.status_label.set_text(t["notice_max"] if full else t["notice_auto"])
        return True

    def set_mode(self, full_speed):
        if self.applying:
            return
        current = read_full_speed()
        if current == full_speed:
            self.refresh()
            return
        self.applying = True
        self.status_label.set_text(TEXT[self.language]["updating"])
        self.auto_button.set_sensitive(False)
        self.max_button.set_sensitive(False)
        self.menu_auto.set_sensitive(False)
        self.menu_max.set_sensitive(False)
        mode = "max" if full_speed else "auto"
        threading.Thread(target=self.run_helper, args=(mode,), daemon=True).start()

    def run_helper(self, mode):
        try:
            result = subprocess.run(
                ["pkexec", HELPER, mode],
                capture_output=True,
                text=True,
                timeout=45,
                check=False,
            )
            message = result.stderr.strip() or result.stdout.strip()
            ok = result.returncode == 0
            if not message:
                message = TEXT[self.language]["updated"] if ok else TEXT[self.language]["failed"]
        except (OSError, subprocess.TimeoutExpired) as exc:
            ok = False
            message = str(exc)
        GLib.idle_add(self.finish_apply, ok, message)

    def finish_apply(self, ok, message):
        self.applying = False
        self.auto_button.set_sensitive(True)
        self.max_button.set_sensitive(True)
        self.menu_auto.set_sensitive(True)
        self.menu_max.set_sensitive(True)
        if not ok:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=TEXT[self.language]["failed"],
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()
        self.refresh()
        return False


if __name__ == "__main__":
    T2FanTray()
    Gtk.main()
