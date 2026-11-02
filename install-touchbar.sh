#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
helper="/usr/local/libexec/t2fantray-helper"

if ! command -v tiny-dfr >/dev/null 2>&1; then
  echo "tiny-dfr chưa được cài. Cài tiny-dfr trước rồi chạy lại script này." >&2
  exit 1
fi
if [[ ! -x "$helper" ]]; then
  echo "Chưa cài helper mới của T2 Fan Control. Hãy chạy sudo ./install.sh trước." >&2
  exit 1
fi

sudo install -m 644 "$script_dir/fan-auto-white.svg" /etc/tiny-dfr/fan_auto_white.svg
sudo install -m 644 "$script_dir/fan-max-red.svg" /etc/tiny-dfr/fan_max_red.svg
sudo "$helper" touchbar-hide

echo "Đã cài icon quạt trắng/đỏ. Trong Settings → Keyboard → Custom Shortcuts, tạo:"
echo "T2 Fan Toggle | pkexec /usr/local/libexec/t2fantray-helper toggle | Ctrl+Shift+F11"
echo "Nút Touch Bar chỉ hiện khi T2 Fan Control chạy ở khay và đổi màu theo chế độ quạt."
