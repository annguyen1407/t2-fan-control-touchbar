#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 || -z ${SUDO_USER:-} ]]; then
  echo "Chạy bằng: sudo $0" >&2
  exit 1
fi

user_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
if [[ -z "$user_home" ]]; then
  echo "Không tìm được thư mục home của $SUDO_USER" >&2
  exit 1
fi

app_dir="/usr/local/lib/t2fantray"
install -d -m 755 "$app_dir" /usr/local/libexec
install -m 755 "$(dirname "$0")/t2fantray.py" "$app_dir/t2fantray.py"
install -m 755 "$(dirname "$0")/t2fantray-helper" /usr/local/libexec/t2fantray-helper
icon_dir="/usr/share/icons/hicolor/scalable/apps"
install -d -m 755 "$icon_dir"
install -m 644 "$(dirname "$0")/t2fantray.svg" "$icon_dir/t2fantray.svg"
install -m 644 "$(dirname "$0")/fan-auto-white.svg" "$icon_dir/t2fantray-auto.svg"
install -m 644 "$(dirname "$0")/fan-max-red.svg" "$icon_dir/t2fantray-max.svg"

cat > /usr/share/applications/t2fantray.desktop <<EOF
[Desktop Entry]
Type=Application
Name=T2 Fan Control
Comment=Điều khiển quạt Mac T2 qua T2FanRD
Exec=/usr/local/lib/t2fantray/t2fantray.py
Icon=t2fantray
Terminal=false
Categories=System;HardwareSettings;
EOF

autostart_enabled="$(python3 - "$user_home/.config/t2fantray/preferences.json" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as f:
        enabled = json.load(f).get("autostart_enabled", True)
except (OSError, ValueError, TypeError):
    enabled = True
print("true" if enabled else "false")
PY
)"

if [[ "$autostart_enabled" == "true" ]]; then
  install -d -o "$SUDO_USER" -g "$(id -gn "$SUDO_USER")" -m 755 "$user_home/.config/autostart"
  cat > "$user_home/.config/autostart/t2fantray.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=T2 Fan Control
Comment=Điều khiển quạt Mac T2 qua T2FanRD
Exec=/usr/local/lib/t2fantray/t2fantray.py
Icon=t2fantray
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
  chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$user_home/.config/autostart/t2fantray.desktop"
else
  rm -f "$user_home/.config/autostart/t2fantray.desktop"
fi
gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true

policy_path="/usr/share/polkit-1/actions/org.t2fantray.policy"
policy_marker="/var/lib/t2fantray/polkit-policy-installed"
if [[ ! -e "$policy_path" ]]; then
  cat <<'EOF'

Quyền tuỳ chọn để khỏi nhập mật khẩu mỗi lần đổi chế độ:
Tài khoản desktop đang đăng nhập có thể gọi helper root đã cài đặt để
chỉ bật quạt tối đa hoặc trả về tự động. Helper không nhận lệnh tuỳ ý.
Đây là quyền quản trị bền vững trong phiên desktop đang hoạt động.
EOF
  answer="n"
  if [[ -r /dev/tty ]]; then
    read -r -p "Cài quyền Polkit này? [y/N] " answer </dev/tty
  fi
  if [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]; then
    install -m 644 "$(dirname "$0")/org.t2fantray.policy" "$policy_path"
    install -d -m 755 /var/lib/t2fantray
    touch "$policy_marker"
    echo "Đã bật quyền đổi chế độ quạt không cần mật khẩu."
  else
    echo "Bỏ qua; ứng dụng sẽ tiếp tục hỏi xác thực mỗi lần đổi chế độ."
  fi
else
  if cmp -s "$(dirname "$0")/org.t2fantray.policy" "$policy_path"; then
    install -d -m 755 /var/lib/t2fantray
    touch "$policy_marker"
  fi
  echo "Quyền Polkit không cần mật khẩu đã có sẵn."
fi

echo "Đã cập nhật T2 Fan Control. Đăng xuất/đăng nhập lại hoặc chạy ứng dụng từ danh sách ứng dụng."
