import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLineEdit, 
                             QLabel, QTextEdit, QGroupBox, QSystemTrayIcon, QMenu, QAction, QFileDialog, QMessageBox)
from PyQt5.QtWidgets import QSystemTrayIcon
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
import psutil
from ram_limiter import limit_ram_for_process, print_system_memory
import pyqtgraph as pg

class RAMLimiterThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, process_name, interval, max_memory_percent):
        QThread.__init__(self)
        self.process_name = process_name
        self.interval = interval
        self.max_memory_percent = max_memory_percent

    def run(self):
        limit_ram_for_process(self.process_name, self.interval, self.max_memory_percent)

class SystemMemoryThread(QThread):
    update_signal = pyqtSignal(str, float)

    def run(self):
        while True:
            mem = psutil.virtual_memory()
            self.update_signal.emit(
                f"System Memory: {mem.percent}% used | {mem.used / (1024 * 1024):.2f} MB used | {mem.available / (1024 * 1024):.2f} MB available",
                mem.percent
            )
            self.sleep(1)

class RAMLimiterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.limiter_threads = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Process selection
        self.process_group = QGroupBox("Select Processes")
        process_layout = QVBoxLayout()
        self.process_checkboxes = {
            "discord": QCheckBox("Discord"),
            "chrome": QCheckBox("Chrome"),
            "obs64": QCheckBox("OBS"),
            "Code": QCheckBox("Visual Studio Code")
        }
        for checkbox in self.process_checkboxes.values():
            process_layout.addWidget(checkbox)
        self.custom_process = QLineEdit()
        self.custom_process.setPlaceholderText("Enter custom process name")
        process_layout.addWidget(self.custom_process)
        self.process_group.setLayout(process_layout)
        layout.addWidget(self.process_group)

        # Minimize to tray button
        self.minimize_button = QPushButton("Minimize to Tray")
        self.minimize_button.clicked.connect(self.minimize_to_tray)
        layout.addWidget(self.minimize_button)

        # Interval and memory percentage inputs
        input_layout = QHBoxLayout()
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Interval (seconds)")
        self.memory_percent_input = QLineEdit()
        self.memory_percent_input.setPlaceholderText("Max memory %")
        input_layout.addWidget(self.interval_input)
        input_layout.addWidget(self.memory_percent_input)
        layout.addLayout(input_layout)

        # Start and Stop buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.start_limiting)
        self.stop_button.clicked.connect(self.stop_limiting)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # Save and Load configuration buttons
        config_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save Configuration")
        self.load_config_button = QPushButton("Load Configuration")
        self.save_config_button.clicked.connect(self.save_configuration)
        self.load_config_button.clicked.connect(self.load_configuration)
        config_layout.addWidget(self.save_config_button)
        config_layout.addWidget(self.load_config_button)
        layout.addLayout(config_layout)

        # Auto-start checkbox
        self.auto_start_checkbox = QCheckBox("Auto-start on application launch")
        layout.addWidget(self.auto_start_checkbox)
        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        # System memory display
        self.system_memory_label = QLabel()
        layout.addWidget(self.system_memory_label)

        # Memory usage graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("System Memory Usage")
        self.graph_widget.setLabel('left', 'Usage (%)')
        self.graph_widget.setLabel('bottom', 'Time (s)')
        self.graph_widget.showGrid(x=True, y=True)
        self.curve = self.graph_widget.plot(pen='b')
        self.data = []
        layout.addWidget(self.graph_widget)
        self.setLayout(layout)
        self.setWindowTitle('RAM Limiter')
        self.show()

        # Initialize system memory thread
        self.system_memory_thread = SystemMemoryThread()
        self.system_memory_thread.update_signal.connect(self.update_system_memory)
        self.system_memory_thread.start()

        # System tray icon
        # System tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('ram.ico'))
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage("RAM Limiter", "Application minimized to tray", QSystemTrayIcon.Information, 2000)

    def start_limiting(self):
        interval = int(self.interval_input.text() or "5")
        max_memory_percent = int(self.memory_percent_input.text() or "75")

        for process_name, checkbox in self.process_checkboxes.items():
            if checkbox.isChecked():
                self.start_limiter_thread(process_name, interval, max_memory_percent)

        custom_process = self.custom_process.text()
        if custom_process:
            self.start_limiter_thread(custom_process, interval, max_memory_percent)

    def start_limiter_thread(self, process_name, interval, max_memory_percent):
        if process_name not in self.limiter_threads or not self.limiter_threads[process_name].isRunning():
            thread = RAMLimiterThread(process_name, interval, max_memory_percent)
            thread.update_signal.connect(self.update_output)
            thread.start()
            self.limiter_threads[process_name] = thread
            self.output_area.append(f"Started limiting RAM for {process_name}")
    def stop_limiting(self):
        for thread in self.limiter_threads.values():
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        self.limiter_threads.clear()
        self.output_area.append("Stopped all RAM limiting")

    def update_output(self, message):
        self.output_area.append(message)

    def update_system_memory(self, message, usage):
        self.system_memory_label.setText(message)
        self.data.append(usage)
        if len(self.data) > 100:  # Keep only last 100 points
            self.data = self.data[-100:]
        self.curve.setData(self.data)

    def save_configuration(self):
        config = {
            "processes": {name: checkbox.isChecked() for name, checkbox in self.process_checkboxes.items()},
            "custom_process": self.custom_process.text(),
            "interval": self.interval_input.text(),
            "max_memory_percent": self.memory_percent_input.text(),
            "auto_start": self.auto_start_checkbox.isChecked()
        }
        filename, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'w') as f:
                json.dump(config, f)
            self.output_area.append(f"Configuration saved to {filename}")

    def load_configuration(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                config = json.load(f)
            for name, checked in config["processes"].items():
                if name in self.process_checkboxes:
                    self.process_checkboxes[name].setChecked(checked)
            self.custom_process.setText(config["custom_process"])
            self.interval_input.setText(config["interval"])
            self.memory_percent_input.setText(config["max_memory_percent"])
            self.auto_start_checkbox.setChecked(config["auto_start"])
            self.output_area.append(f"Configuration loaded from {filename}")

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            reply = QMessageBox.question(self, 'Minimize', 'Do you want to minimize to tray?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage("RAM Limiter", "Application minimized to tray", QSystemTrayIcon.Information, 2000)
            else:
                reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.stop_limiting()
                    event.accept()
                else:
                    event.ignore()
        else:
            self.stop_limiting()
            event.accept()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RAMLimiterGUI()
    sys.exit(app.exec_())

