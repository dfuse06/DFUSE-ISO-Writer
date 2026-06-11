# DFUSE ISO Writer

A Linux ISO-to-USB writing utility built with Python and PySide6.

Create bootable USB drives from Linux ISO images using a simple graphical interface.

---

## Features

* Automatic USB detection
* Bootable USB creation
* Real-time progress tracking
* DFUSE Purple Neon Theme
* PySide6 GUI
* Linux-first design
* Uses PolicyKit for privilege escalation

---

# Screenshots

## Startup

![DFUSE ISO Writer Startup](screenshots/iso.png)

## ISO Selected

![DFUSE ISO Writer ISO Selected](screenshots/iso2.png)

## Writing Process

![DFUSE ISO Writer Writing](screenshots/iso3.png)

## Completed Write

![DFUSE ISO Writer Complete](screenshots/iso4.png)

---

## Requirements

### Arch Linux / EndeavourOS

```bash
sudo pacman -S python pyside6 polkit
```

### Ubuntu / Debian

```bash
sudo apt install python3 python3-pyside6 policykit-1
```

---

## Run

```bash
git clone https://github.com/dfuse06/DFUSE-ISO-Writer.git
cd DFUSE-ISO-Writer

python main.py
```

---

## Usage

1. Insert USB drive
2. Select ISO
3. Select USB device
4. Click **Write ISO to USB**
5. Enter administrator password
6. Wait for completion
7. Boot from the USB

---

## Warning

Writing an ISO will erase all data on the selected USB device.

Always verify the selected device before continuing.

---

## Author

Dustin Winings (dfuse)

GitHub: https://github.com/dfuse06
