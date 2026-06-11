import os
import re
import sys
import subprocess

from PySide6.QtCore import QThread, Signal

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
)

from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


class WriterThread(QThread):
    progress = Signal(int)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, iso_path, device):
        super().__init__()
        self.iso_path = iso_path
        self.device = device

    def run(self):
        iso_size = os.path.getsize(self.iso_path)

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
                match = re.search(r"(\d+)\s+bytes", line)
                if match:
                    written = int(match.group(1))
                    percent = int((written / iso_size) * 100)
                    self.progress.emit(min(percent, 100))

            if process.poll() is not None:
                break

        stderr_output = process.stderr.read()

        if process.returncode == 0:
            self.progress.emit(100)
            subprocess.run(["sync"])
            self.finished_ok.emit()
        else:
            self.failed.emit(stderr_output or "ISO write failed.")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DFUSE ISO Writer v0.1")
        self.resize(700, 500)

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

        self.progress = QProgressBar()
        self.progress.setValue(0)
        

        layout.addWidget(self.title)
        layout.addWidget(self.iso_label)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.drive_label)
        layout.addWidget(self.drive_box)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.write_btn)
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.load_drives()

    def select_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ISO",
            "",
            "ISO Files (*.iso)"
        )

        if file_path:
            self.iso_path = file_path
            self.iso_label.setText(os.path.basename(file_path))
            self.progress.setValue(0)

    def load_drives(self):
        self.drive_box.clear()

        result = subprocess.run(
            ["lsblk", "-dn", "-o", "NAME,SIZE,TRAN,TYPE"],
            capture_output=True,
            text=True
        )

        found_usb = False

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) >= 4:
                name = parts[0]
                size = parts[1]
                tran = parts[2]
                dev_type = parts[3]

                if tran == "usb" and dev_type == "disk":
                    device = f"/dev/{name}"
                    self.drive_box.addItem(f"{device} ({size})", device)
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
            f"This will erase everything on:\n\n{device}\n\nContinue?"
        )

        if confirm != QMessageBox.Yes:
            return

        self.progress.setValue(0)
        self.select_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        self.drive_box.setEnabled(False)

        self.writer_thread = WriterThread(self.iso_path, device)
        self.writer_thread.progress.connect(self.progress.setValue)
        self.writer_thread.finished_ok.connect(self.write_finished)
        self.writer_thread.failed.connect(self.write_failed)
        self.writer_thread.start()

    def write_finished(self):
        self.select_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        self.drive_box.setEnabled(True)

        QMessageBox.information(
            self,
            "Done",
            "ISO successfully written to USB.\n\nYou can safely remove it now."
        )

    def write_failed(self, error):
        self.select_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.write_btn.setEnabled(True)
        self.drive_box.setEnabled(True)

        QMessageBox.critical(
            self,
            "Failed",
            error
        )


app = QApplication(sys.argv)

with open("themes/dfuse_dark.qss", "r") as theme:
    app.setStyleSheet(theme.read())

window = MainWindow()
window.show()

sys.exit(app.exec())