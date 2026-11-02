# T2 Fan Control

[![Tiếng Việt](https://img.shields.io/badge/Ng%C3%B4n_ng%E1%BB%AF-Ti%E1%BA%BFng_Vi%E1%BB%87t-2ea44f)](README_VI.md)
[![English](https://img.shields.io/badge/Language-English-lightgrey)](../README.md)

**T2 Fan Control** là ứng dụng khay hệ thống nhỏ cho MacBook có chip T2, chạy Ubuntu/GNOME và dùng [T2FanRD](https://github.com/GnomedDev/T2FanRD) để điều khiển quạt. Ứng dụng có dashboard RPM, chế độ Auto/Max, icon khay đổi màu, tùy chọn tự khởi động và tích hợp tùy chọn với Touch Bar qua `tiny-dfr`.

> Dự án được phát triển cho cấu hình Ubuntu 26.04, GNOME 50, Wayland, T2FanRD và `tiny-dfr`. Các bản phân phối hoặc phiên bản khác có thể cần điều chỉnh.

## Tính năng

- Dashboard gọn hiển thị RPM hiện tại và phần trăm tối đa của từng quạt.
- Chuyển giữa đường cong tự động của T2FanRD và tốc độ tối đa.
- Icon khay desktop màu trắng ở Auto, đỏ ở Max.
- Trang cài đặt chọn tiếng Việt/tiếng Anh, bật/tắt nút Touch Bar và tự khởi động cùng Ubuntu.
- Một nút quạt trên Touch Bar: trắng ở Auto, đỏ ở Max; nằm bên trái pin, còn pin và đồng hồ nằm ở mép ngoài.
- Cấu hình tiny-dfr được nạp lại trực tiếp khi đổi màu hoặc hiện/ẩn nút; không restart `tiny-dfr` mỗi lần.
- Dùng Polkit helper chỉ nhận các thao tác giới hạn `auto`, `max`, `toggle`, `touchbar-show`, `touchbar-hide`.

## Yêu cầu

- MacBook hỗ trợ T2 và driver quạt `macsmc_hwmon`.
- Ubuntu/GNOME; giao diện dùng GTK 3 và Ayatana AppIndicator.
- [T2FanRD](https://github.com/GnomedDev/T2FanRD) đã cài, với dịch vụ `t2fanrd.service` và `/etc/t2fand.conf`.
- Python 3, `python3-gi`, Ayatana AppIndicator.
- Tích hợp Touch Bar: `tiny-dfr` 0.3.7 trở lên và cấu hình `/etc/tiny-dfr/config.toml`.

## Cài đặt

Tải hoặc clone repository rồi chạy trong thư mục dự án:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1
sudo bash ./install.sh
```

`install.sh` cần chạy qua `sudo` để cài app, helper, desktop entry, autostart và icon hệ thống. Script có thể hỏi bạn có muốn cài quyền Polkit để đổi chế độ không cần nhập mật khẩu không. Nếu từ chối, Polkit sẽ xác thực khi helper được gọi.

Sau khi cài:

1. Đăng xuất rồi đăng nhập lại, hoặc mở **T2 Fan Control** từ danh sách ứng dụng.
2. Icon quạt xuất hiện ở khu vực khay hệ thống.
3. Mở dashboard để xem RPM và chọn Auto/Max. Đóng cửa sổ sẽ ẩn dashboard xuống khay; chọn **Quit/Thoát** trong menu khay để dừng app.

## Cài Touch Bar

### 1. Cài tiny-dfr

Cài `tiny-dfr` theo hướng dẫn của T2Linux. Tổ hợp phím trong cấu hình Touch Bar cần tiny-dfr 0.3.7 trở lên. Kiểm tra phiên bản:

```bash
tiny-dfr --version
```

Nếu Ubuntu cung cấp bản cũ, script tùy chọn `update-tiny-dfr.sh` build tag chính thức v0.3.7 bằng Cargo và cài systemd override. Nó cần kết nối mạng, Cargo/Git, các thư viện build và quyền sudo. Đọc script trước khi chạy:

```bash
bash ./update-tiny-dfr.sh
```

### 2. Cài icon Touch Bar

```bash
bash ./install-touchbar.sh
```

Script cài icon trắng/đỏ. Nó không đăng ký shortcut GNOME tự động: trên hệ thống này, shortcut tạo bằng giao diện GNOME mới hoạt động ổn định.

### 3. Tạo shortcut trong GNOME Settings

Mở **Settings → Keyboard → Custom Shortcuts → Add Shortcut…** và tạo:

| Trường | Giá trị |
|---|---|
| Name | `T2 Fan Toggle` |
| Command | `pkexec /usr/local/libexec/t2fantray-helper toggle` |
| Shortcut | `Ctrl+Shift+F11` |

Mở **T2 Fan Control → Settings** và bật **Touch Bar fan button**. Nút chỉ hiện khi app chạy trong khay; ẩn dashboard không làm mất nút. Khi thoát app, nút được gỡ. Tổ hợp bàn phím và nút Touch Bar gọi cùng shortcut GNOME.

Cấu hình `MediaLayerKeys` đặt nút quạt ngay trước mục Battery và để Battery/Time ở cuối danh sách. Nếu tự chỉnh `/etc/tiny-dfr/config.toml`, giữ thứ tự này để duy trì vị trí.

## Cách hoạt động

- GUI đọc `always_full_speed` từ các section Fan trong `/etc/t2fand.conf` và đọc RPM từ `macsmc_hwmon` trong `/sys/class/hwmon`.
- Helper cập nhật cấu hình T2FanRD, rồi restart `t2fanrd.service` để áp dụng chế độ.
- Với Touch Bar, helper sửa icon trong `/etc/tiny-dfr/config.toml` tại chỗ để `tiny-dfr` nạp lại cấu hình qua inotify; daemon Touch Bar không bị restart khi đổi chế độ.
- `~/.config/t2fantray/preferences.json` lưu ngôn ngữ và tùy chọn nút Touch Bar. Autostart được lưu ở `~/.config/autostart/t2fantray.desktop`.

## Nâng cấp

Lấy phiên bản mới của source, sau đó cài lại app và icon Touch Bar:

```bash
git pull
sudo bash ./install.sh
bash ./install-touchbar.sh
```

Thoát hoàn toàn T2 Fan Control rồi mở lại để tiến trình nạp code mới. Shortcut GNOME `T2 Fan Toggle` vẫn được giữ lại.

## Gỡ cài đặt

Thoát T2 Fan Control, rồi chạy:

```bash
sudo bash ./uninstall.sh
```

Script gỡ app, helper, desktop/autostart entries, Polkit policy và icon của dự án; đồng thời gỡ nút quạt khỏi cấu hình tiny-dfr nếu helper còn cài. T2FanRD, tiny-dfr và `/etc/t2fand.conf` vẫn được giữ lại. Shortcut `T2 Fan Toggle` do bạn tạo trong GNOME Settings cần xóa thủ công ở **Custom Shortcuts**. Tùy chọn người dùng trong `~/.config/t2fantray/` được giữ lại.

## Khắc phục sự cố

Xem [hướng dẫn xử lý sự cố](TROUBLESHOOTING.md) để kiểm tra app, dịch vụ, shortcut GNOME và tiny-dfr.

## Đóng góp

Xem [CONTRIBUTING.md](../CONTRIBUTING.md). Vui lòng không commit thông tin cá nhân, cấu hình `/etc/t2fand.conf`, log có dữ liệu nhạy cảm hoặc file build.

## Nguồn và ghi nhận

Danh mục nguồn, giấy phép phụ thuộc và ghi nhận artwork đầy đủ nằm trong [THIRD_PARTY.md](../THIRD_PARTY.md).

- [T2FanRD](https://github.com/GnomedDev/T2FanRD) — daemon điều khiển quạt mà ứng dụng tích hợp; upstream dùng [GPL-3.0](https://github.com/GnomedDev/T2FanRD/blob/master/LICENCE). T2 Fan Control không chứa mã nguồn T2FanRD.
- [tiny-dfr](https://github.com/AsahiLinux/tiny-dfr) — daemon Touch Bar mà ứng dụng tích hợp; upstream dùng [MIT](https://github.com/AsahiLinux/tiny-dfr/blob/master/LICENSE). Script tùy chọn build tag [v0.3.7](https://github.com/AsahiLinux/tiny-dfr/tree/v0.3.7).
- [T2Linux Wiki: Basic setup](https://wiki.t2linux.org/guides/postinstall/) — hướng dẫn cài tiny-dfr và cấu hình `/etc/tiny-dfr/config.toml` trên Mac T2.
- [GNOME Help: Set keyboard shortcuts](https://help.gnome.org/gnome-help/keyboard-shortcuts-set.html) — hướng dẫn tạo custom shortcut dùng để gọi helper.
- [AyatanaIndicators/libayatana-appindicator](https://github.com/AyatanaIndicators/libayatana-appindicator) — thư viện GTK3 AppIndicator dùng cho icon khay; upstream cung cấp giấy phép [LGPL-3.0](https://github.com/AyatanaIndicators/libayatana-appindicator/blob/main/COPYING).
- [GTK](https://www.gtk.org/) và [PyGObject](https://gitlab.gnome.org/GNOME/pygobject) — toolkit GTK3 và binding Python dùng để dựng giao diện.
- Các tệp SVG `t2fantray.svg`, `fan-auto-white.svg` và `fan-max-red.svg` là tài sản riêng của repository này; không được sao chép từ tiny-dfr.

Các dự án upstream giữ bản quyền và giấy phép riêng. T2 Fan Control là dự án cộng đồng độc lập, không được T2FanRD, AsahiLinux, T2Linux, GNOME hoặc AyatanaIndicators chứng thực.

## Giấy phép

Chưa gắn giấy phép phát hành. Trước khi public, chọn một license và thêm file `LICENSE`; nếu không có license, người khác không được mặc định quyền sao chép, sửa đổi hoặc phân phối mã nguồn.
