import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLineEdit,
                             QLabel, QTextEdit, QGroupBox, QSystemTrayIcon, QMenu, QAction, QFileDialog, QMessageBox, QGridLayout, QProgressBar, QInputDialog)
from PyQt5.QtCore import QThread, pyqtSignal, QMetaType, Qt
from PyQt5.QtGui import QIcon
import psutil
from ram_limiter import limit_ram_for_process
import pyqtgraph as pg

# Register QVector<int> metatype to fix Qt signal/slot warnings across threads
# This is required for pyqtgraph when emitting signals with QVector<int> arguments
try:
    QMetaType.type("QVector<int>")
except:
    pass

class RAMLimiterThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, process_name, interval, max_memory_percent):
        QThread.__init__(self)
        self.process_name = process_name
        self.interval = interval
        self.max_memory_percent = max_memory_percent

    def run(self):
        limit_ram_for_process(self.process_name, self.interval, self.max_memory_percent)

class GameModeThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, ram_limit_mb, whitelist):
        super().__init__()
        self.ram_limit_mb = ram_limit_mb
        self.whitelist = whitelist
        self.running = True

    def run(self):
        while self.running:
            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    if proc.name().lower() not in self.whitelist:
                        memory_mb = proc.memory_info().rss / (1024 * 1024)
                        if memory_mb > self.ram_limit_mb:
                            proc.kill()
                            self.update_signal.emit(f"Killed process {proc.name()} using {memory_mb:.2f} MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self.sleep(2)

    def stop(self):
        self.running = False

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
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI';
            }
            QGroupBox {
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: #00b4d8;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #5a5a5a;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QLineEdit {
                background-color: #353535;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #353535;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Process selection with grid layout
        self.process_group = QGroupBox("Process Selection")
        process_layout = QGridLayout()
        self.process_checkboxes = {
            "discord": QCheckBox("Discord"),
            "chrome": QCheckBox("Chrome"),
            "obs64": QCheckBox("OBS"),
            "Code": QCheckBox("Visual Studio Code"),
            "msedge": QCheckBox("Microsoft Edge")
        }
        checkboxes = list(self.process_checkboxes.values())
        for i, checkbox in enumerate(checkboxes):
            row = i // 2
            col = i % 2
            process_layout.addWidget(checkbox, row, col)

        # Custom process input with icon
        custom_layout = QHBoxLayout()
        self.custom_process = QLineEdit()
        self.custom_process.setPlaceholderText("Enter custom process name...")
        self.custom_process_limit = QLineEdit()
        self.custom_process_limit.setPlaceholderText("Custom process memory limit (%)")

        custom_layout.addWidget(QLabel("Custom Process:"))
        custom_layout.addWidget(self.custom_process)
        custom_layout.addWidget(QLabel("Memory Limit (%):"))
        custom_layout.addWidget(self.custom_process_limit)

        process_layout.addLayout(custom_layout, len(self.process_checkboxes) // 2 + 1, 0, 1, 2)
        self.process_group.setLayout(process_layout)
        layout.addWidget(self.process_group)

        # Styled buttons
        self.minimize_button = QPushButton("🎯 Minimize to Tray")
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.minimize_button.clicked.connect(self.minimize_to_tray)
        layout.addWidget(self.minimize_button)

        # Gradient buttons for start/stop
        self.start_button = QPushButton("🚀 Start Monitoring")
        self.stop_button = QPushButton("🛑 Stop All")
        for btn in [self.start_button, self.stop_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2980b9, stop:1 #3498db);
                }
            """)
        self.start_button.clicked.connect(self.start_limiting)
        self.stop_button.clicked.connect(self.stop_limiting)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # Input fields with labels
        input_layout = QHBoxLayout()
        self.interval_input = QLineEdit()
        self.memory_percent_input = QLineEdit()
        for widget, label in [(self.interval_input, "Interval (s):"),
                            (self.memory_percent_input, "Max Memory (%):")]:
            container = QHBoxLayout()
            container.addWidget(QLabel(label))
            container.addWidget(widget)
            input_layout.addLayout(container)
        layout.addLayout(input_layout)

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

        # Add animated progress bar for memory usage
        self.memory_progress = QProgressBar()
        self.memory_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00b4d8;
                width: 10px;
            }
        """)
        layout.addWidget(self.memory_progress)

        self.setLayout(layout)
        self.setWindowTitle('RAM Limiter')
        self.show()

        # Initialize system memory thread
        self.system_memory_thread = SystemMemoryThread()
        self.system_memory_thread.update_signal.connect(self.update_system_memory)
        self.system_memory_thread.start()

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

        # Initialize game mode UI
        self.init_game_mode()

    def init_game_mode(self):
        self.game_mode_group = QGroupBox("Game Mode")
        game_mode_layout = QVBoxLayout()

        self.game_mode_checkbox = QCheckBox("Enable Game Mode")
        self.game_mode_checkbox.stateChanged.connect(self.toggle_game_mode)

        self.game_whitelist = QLineEdit()
        self.game_whitelist.setPlaceholderText("Whitelist (comma-separated processes)")

        self.ram_limit_input = QLineEdit()
        self.ram_limit_input.setPlaceholderText("RAM limit per process (MB)")
        self.ram_limit_input.setText("500")

        game_mode_layout.addWidget(self.game_mode_checkbox)
        game_mode_layout.addWidget(QLabel("RAM Limit (MB):"))
        game_mode_layout.addWidget(self.ram_limit_input)
        game_mode_layout.addWidget(QLabel("Whitelist:"))
        game_mode_layout.addWidget(self.game_whitelist)

        self.game_mode_group.setLayout(game_mode_layout)
        self.layout().addWidget(self.game_mode_group)

        self.game_mode_thread = None

    def toggle_game_mode(self, state):
        if state:
            try:
                ram_limit = int(self.ram_limit_input.text())
                whitelist = [proc.strip().lower() for proc in self.game_whitelist.text().split(',')]

                system_processes = ['explorer.exe', 'system', 'systemd', 'svchost.exe',
                                    'csrss.exe', 'winlogon.exe', 'services.exe']
                whitelist.extend(system_processes)

                self.game_mode_thread = GameModeThread(ram_limit, whitelist)
                self.game_mode_thread.update_signal.connect(self.update_output)
                self.game_mode_thread.start()
                self.output_area.append("Game Mode activated")
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid RAM limit")
                self.game_mode_checkbox.setChecked(False)
        else:
            if self.game_mode_thread:
                self.game_mode_thread.stop()
                self.game_mode_thread.wait()
                self.game_mode_thread = None
                self.output_area.append("Game Mode deactivated")

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
            # Use custom limit if provided, otherwise use the global limit
            custom_limit = self.custom_process_limit.text()
            if custom_limit:
                try:
                    custom_memory_percent = int(custom_limit)
                    self.start_limiter_thread(custom_process, interval, custom_memory_percent)
                except ValueError:
                    self.update_output(f"Invalid custom memory limit: {custom_limit}. Using global limit.")
                    self.start_limiter_thread(custom_process, interval, max_memory_percent)
            else:
                self.start_limiter_thread(custom_process, interval, max_memory_percent)

    def start_limiter_thread(self, process_name, interval, max_memory_percent):
        if process_name not in self.limiter_threads or not self.limiter_threads[process_name].isRunning():
            thread = RAMLimiterThread(process_name, interval, max_memory_percent)
            thread.update_signal.connect(self.update_output)
            thread.start()
            self.limiter_threads[process_name] = thread
            self.output_area.append(f"Started limiting RAM for {process_name} (Max: {max_memory_percent}%)")

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
        self.memory_progress.setValue(int(usage))

    def save_configuration(self):
        config = {
            "processes": {name: checkbox.isChecked() for name, checkbox in self.process_checkboxes.items()},
            "custom_process": self.custom_process.text(),
            "custom_process_limit": self.custom_process_limit.text(),
            "interval": self.interval_input.text(),
            "max_memory_percent": self.memory_percent_input.text(),
            "auto_start": self.auto_start_checkbox.isChecked(),
            "game_mode": {
                "enabled": self.game_mode_checkbox.isChecked(),
                "ram_limit": self.ram_limit_input.text(),
                "whitelist": self.game_whitelist.text()
            }
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
            if "custom_process_limit" in config:
                self.custom_process_limit.setText(config["custom_process_limit"])
            self.interval_input.setText(config["interval"])
            self.memory_percent_input.setText(config["max_memory_percent"])
            self.auto_start_checkbox.setChecked(config["auto_start"])
            if "game_mode" in config:
                self.game_mode_checkbox.setChecked(config["game_mode"]["enabled"])
                self.ram_limit_input.setText(config["game_mode"]["ram_limit"])
                self.game_whitelist.setText(config["game_mode"]["whitelist"])
            self.output_area.append(f"Configuration loaded from {filename}")

    def closeEvent(self, event):
        if self.game_mode_thread:
            self.game_mode_thread.stop()
            self.game_mode_thread.wait()
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

