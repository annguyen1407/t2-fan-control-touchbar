#!/usr/bin/env bash
set -euo pipefail

version="0.3.7"
workdir="$(mktemp -d -t tiny-dfr-build.XXXXXX)"
cleanup() { rm -rf "$workdir"; }
trap cleanup EXIT

if ! command -v cargo >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
  echo "Cần cài cargo và git trước." >&2
  exit 1
fi

sudo apt-get install -y --no-install-recommends \
  build-essential pkg-config libinput-dev libcairo2-dev \
  libfreetype-dev libfontconfig1-dev librsvg2-dev libudev-dev

git clone --depth 1 --branch "v$version" \
  https://github.com/AsahiLinux/tiny-dfr.git "$workdir/source"
cargo build --release --manifest-path "$workdir/source/Cargo.toml"

binary="$workdir/source/target/release/tiny-dfr"
if [[ ! -x "$binary" ]]; then
  echo "Không tìm thấy binary tiny-dfr sau khi build." >&2
  exit 1
fi

sudo install -D -m 755 "$binary" "/usr/local/libexec/tiny-dfr-$version"
override_dir="/etc/systemd/system/tiny-dfr.service.d"
override_file="$override_dir/zz-local-version.conf"
if [[ -e "$override_file" ]]; then
  echo "Đã tồn tại $override_file; giữ nguyên để tránh ghi đè cấu hình riêng." >&2
  exit 1
fi
sudo install -d -m 755 "$override_dir"
sudo tee "$override_file" >/dev/null <<EOF
[Service]
ExecStart=
ExecStart=/usr/local/libexec/tiny-dfr-$version
EOF

sudo systemctl daemon-reload
if ! sudo systemctl restart tiny-dfr.service; then
  sudo rm -f "$override_file"
  sudo systemctl daemon-reload
  sudo systemctl restart tiny-dfr.service || true
  echo "tiny-dfr $version không khởi động được; đã gỡ override để quay về bản Ubuntu." >&2
  exit 1
fi

echo "Đã cài tiny-dfr $version vào /usr/local/libexec và khởi động lại dịch vụ."
