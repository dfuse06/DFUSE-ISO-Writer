import os
import re
import sys
import time
import subprocess

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QComboBox,
    QMessageBox,
    QProgressBar,
    QGraphicsDropShadowEffect,
)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class WriterThread(QThread):
    progress = Signal(int)
    stats = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, iso_path, device):
        super().__init__()
        self.iso_path = iso_path
        self.device = device

    def run(self):
        iso_size = os.path.getsize(self.iso_path)
        start_time = time.time()

        command = [
            "pkexec",
            "dd",
            f"if={self.iso_path}",
            f"of={self.device}",
            "bs=4M",
            "status=progress",
            "conv=fsync",
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        while True:
            line = process.stderr.readline()

            if line:
                match = re.search(r"(\\d+)\\s+bytes", line)

                if match:
                    written = int(match.group(1))
                    elapsed = max(time.time() - start_time, 1)

                    percent = int((written / iso_size) * 100)
                    speed_mbs = (written / elapsed) / (1024 * 1024)

                    remaining_bytes = max(iso_size - written, 0)

                    if speed_mbs > 0:
                        eta_seconds = remaining_bytes / (speed_mbs * 1024 * 1024)
                    else:
                        eta_seconds = 0

                    eta_text = self.format_time(eta_seconds)

                    self.progress.emit(min(percent, 100))
                    self.stats.emit(
                        f"Speed: {speed_mbs:.1f} MB/s  |  ETA: {eta_text}"
                    )

            if process.poll() is not None:
                break

        stderr_output = process.stderr.read()

        if process.returncode == 0:
            self.progress.emit(100)
            self.stats.emit("Speed: Complete  |  ETA: 0s")
            subprocess.run(["sync"])
            self.finished_ok.emit()
        else:
            self.failed.emit(stderr_output or "ISO write failed.")

    def format_time(self, seconds):
        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds}s"

        minutes = seconds // 60
        seconds = seconds % 60

        if minutes < 60:
            return f"{minutes}m {seconds}s"

        hours = minutes // 60
        minutes = minutes % 60

        return f"{hours}h {minutes}m"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DFUSE ISO Writer v0.1")
        self.resize(700, 520)
        self.setWindowIcon(QIcon(resource_path("dfuse_iso.png")))

        self.iso_path = ""
        self.writer_thread = None

        layout = QVBoxLayout()

        self.title = QLabel("DFUSE ISO Writer v0.1")
        self.title.setObjectName("title")

        self.iso_label = QLabel("No ISO Selected")

        self.select_btn = QPushButton("Select ISO")
        self.select_btn.clicked.connect(self.select_iso)

        self.drive_label = QLabel("USB Device:")
        self.drive_box = QComboBox()

        self.refresh_btn = QPushButton("Refresh USB Devices")
        self.refresh_btn.clicked.connect(self.load_drives)

        self.write_btn = QPushButton("Write ISO to USB")
        self.write_btn.clicked.connect(self.write_iso)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setColor(QColor("#a855f7"))
        glow.setOffset(0)
        self.write_btn.setGraphicsEffect(glow)

        self.stats_label = QLabel("Speed: -- MB/s  |  ETA: --")
        self.stats_label.setObjectName("stats")

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%p%")

        layout.addWidget(self.title)
        layout.addWidget(self.iso_label)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.drive_label)
        layout.addWidget(self.drive_box)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.write_btn)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.load_drives()

    def select_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ISO",
            "",
            "ISO Files (*.iso)",
        )

        if file_path:
            self.iso_path = file_path
            size_gb = os.path.getsize(file_path) / (1024 ** 3)
            self.iso_label.setText(
                f"{os.path.basename(file_path)} | {size_gb:.2f} GB"
            )
            self.progress.setValue(0)
            self.stats_label.setText("Speed: -- MB/s  |  ETA: --")

    def load_drives(self):
        self.drive_box.clear()

        result = subprocess.run(
            ["lsblk", "-dn", "-o", "NAME,SIZE,TRAN,TYPE,MODEL,VENDOR"],
            capture_output=True,
            text=True,
        )

        found_usb = False

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) >= 4:
                name = parts[0]
                size = parts[1]
                tran = parts[2]
                dev_type = parts[3]
                extra_info = " ".join(parts[4:]) if len(parts) > 4 else "Unknown USB"

                if tran == "usb" and dev_type == "disk":
                    device = f"/dev/{name}"
                    display_text = f"{device} | {size} | {extra_info}"
                    self.drive_box.addItem(display_text, device)
                    found_usb = True

        if not found_usb:
            self.drive_box.addItem("No USB devices found", None)

    def write_iso(self):
        if not self.iso_path:
            QMessageBox.warning(self, "No ISO", "Select an ISO first.")
            return

        device = self.drive_box.currentData()

        if not device:
            QMessageBox.warning(self, "No USB", "No USB device selected.")
            return

        confirm = QMessageBox.question(
            self,
            "WARNING",
            f"This will erase everything on:\\n\\n{device}\\n\\nContinue?",
        )

        if confirm != QMessageBox.Yes:
            return

        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.stats_label.setText("Starting write...")

        self.select_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        self.drive_box.setEnabled(False)

        self.writer_thread = WriterThread(self.iso_path, device)
        self.writer_thread.progress.connect(self.progress.setValue)
        self.writer_thread.stats.connect(self.stats_label.setText)
        self.writer_thread.finished_ok.connect(self.write_finished)
        self.writer_thread.failed.connect(self.write_failed)
        self.writer_thread.start()

    def write_finished(self):
        self.select_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        self.drive_box.setEnabled(True)

        self.stats_label.setText("Write complete.")
        self.progress.setValue(100)

        QMessageBox.information(
            self,
            "Done",
            "ISO successfully written to USB.\\n\\nYou can safely remove it now.",
        )

    def write_failed(self, error):
        self.select_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        self.drive_box.setEnabled(True)

        self.stats_label.setText("Write failed.")
        QMessageBox.critical(self, "Failed", error)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("dfuse_iso.png")))

    with open(resource_path("themes/dfuse_dark.qss"), "r") as theme:
        app.setStyleSheet(theme.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
