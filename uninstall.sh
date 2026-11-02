#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 || -z ${SUDO_USER:-} ]]; then
  echo "Chạy bằng: sudo $0" >&2
  exit 1
fi

user_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
helper="/usr/local/libexec/t2fantray-helper"
policy_marker="/var/lib/t2fantray/polkit-policy-installed"

if [[ -x "$helper" ]]; then
  "$helper" touchbar-hide || true
fi

rm -f /usr/share/applications/t2fantray.desktop
if [[ -e "$policy_marker" ]]; then
  rm -f /usr/share/polkit-1/actions/org.t2fantray.policy "$policy_marker"
  rmdir /var/lib/t2fantray 2>/dev/null || true
fi
rm -f /usr/local/libexec/t2fantray-helper
rm -rf /usr/local/lib/t2fantray
rm -f /usr/share/icons/hicolor/scalable/apps/t2fantray.svg
rm -f /usr/share/icons/hicolor/scalable/apps/t2fantray-auto.svg
rm -f /usr/share/icons/hicolor/scalable/apps/t2fantray-max.svg
gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
rm -f "$user_home/.config/autostart/t2fantray.desktop"
rm -f /etc/tiny-dfr/fan_auto_white.svg /etc/tiny-dfr/fan_max_red.svg
echo "Đã gỡ T2 Fan Control. T2FanRD và cấu hình của nó vẫn được giữ lại."
