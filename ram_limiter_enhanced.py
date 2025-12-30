import os
# Configure pyqtgraph to use PyQt5 explicitly - MUST be set before any Qt imports
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

import sys
import time
import json
import psutil
import ctypes
import argparse
import threading
import logging
import gc
import platform
import socket
import hashlib
import subprocess
import webbrowser
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from ctypes import wintypes
from colorama import init, Fore, Back, Style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLineEdit,
                            QLabel, QTextEdit, QGroupBox, QSystemTrayIcon, QMenu, QAction, QFileDialog,
                            QMessageBox, QGridLayout, QProgressBar, QInputDialog, QComboBox, QSlider,
                            QTabWidget, QStackedWidget, QListWidget, QListWidgetItem, QAbstractItemView,
                            QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QSpinBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QDateTime, QSize, QMetaType

# Import sip to register metatypes BEFORE pyqtgraph import
try:
    from PyQt5 import sip
except ImportError:
    import sip

from PyQt5.QtGui import QIcon, QColor, QPainter, QBrush, QPen, QFont

# Import and configure pyqtgraph AFTER Qt is set up
import pyqtgraph as pg
# Configure pyqtgraph to avoid threading issues
pg.setConfigOptions(useOpenGL=False, antialias=True, exitCleanup=False)

# Windows-specific imports (only available on Windows)
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32process
    except ImportError:
        win32gui = None
        win32process = None
else:
    win32gui = None
    win32process = None

# Initialize colorama
init(autoreset=True)

# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF

class MemoryManagementStrategy(Enum):
    AGGRESSIVE = auto()
    BALANCED = auto()
    CONSERVATIVE = auto()

class ProcessPriority(Enum):
    CRITICAL = auto()
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()
    BACKGROUND = auto()

class PerformanceProfile(Enum):
    BALANCED = "Balanced"
    GAMING = "Gaming"
    WORK = "Work"
    BATTERY_SAVER = "Battery Saver"
    CUSTOM = "Custom"

class SystemHealthStatus(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"

class MemoryOptimizationMode(Enum):
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"
    LEARNING = "Learning"

class NotificationType(Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    SUCCESS = "Success"

class ProcessInfo:
    def __init__(self, pid: int, name: str, memory_usage: float, cpu_usage: float, priority: ProcessPriority = ProcessPriority.NORMAL):
        self.pid = pid
        self.name = name
        self.memory_usage = memory_usage  # in MB
        self.cpu_usage = cpu_usage  # percentage
        self.priority = priority
        self.historical_data = deque(maxlen=100)  # Store last 100 data points
        self.last_updated = datetime.now()

    def update(self, memory_usage: float, cpu_usage: float):
        self.memory_usage = memory_usage
        self.cpu_usage = cpu_usage
        self.historical_data.append((datetime.now(), memory_usage, cpu_usage))
        self.last_updated = datetime.now()

    def get_memory_trend(self) -> float:
        """Calculate memory usage trend (positive = increasing, negative = decreasing)"""
        if len(self.historical_data) < 2:
            return 0.0
        old_value = self.historical_data[0][1]
        new_value = self.historical_data[-1][1]
        return new_value - old_value

class SystemMonitor:
    def __init__(self):
        self.system_info = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_usage': {'sent': 0, 'received': 0},
            'temperature': 0.0,
            'process_count': 0,
            'system_load': [0.0, 0.0, 0.0]  # 1, 5, 15 min averages
        }
        self.process_history = {}
        self.start_time = datetime.now()
        self.uptime = timedelta(0)

    def update_system_info(self):
        """Update comprehensive system information"""
        try:
            # CPU Information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()

            # Memory Information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk Information
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # Network Information
            net_io = psutil.net_io_counters()

            # System Information
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            self.uptime = datetime.now() - boot_time

            # Update system info
            self.system_info.update({
                'cpu_usage': cpu_percent,
                'cpu_frequency': cpu_freq._asdict() if cpu_freq else None,
                'cpu_cores': cpu_count,
                'memory_usage': memory.percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'memory_available': memory.available,
                'swap_usage': swap.percent if swap else 0,
                'disk_usage': disk_usage.percent,
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'network_sent': net_io.bytes_sent,
                'network_received': net_io.bytes_recv,
                'boot_time': boot_time,
                'process_count': len(list(psutil.process_iter()))
            })

            # Update process information
            self._update_process_info()

        except Exception as e:
            logging.error(f"Error updating system info: {e}")

    def _update_process_info(self):
        """Update information about running processes"""
        try:
            current_pids = set()
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    pid = proc.info['pid']
                    current_pids.add(pid)
                    name = proc.info['name']
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    cpu_percent = proc.cpu_percent(interval=0.1)

                    if pid not in self.process_history:
                        self.process_history[pid] = ProcessInfo(pid, name, memory_mb, cpu_percent)
                    else:
                        self.process_history[pid].update(memory_mb, cpu_percent)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Remove processes that no longer exist
            for pid in list(self.process_history.keys()):
                if pid not in current_pids:
                    del self.process_history[pid]

        except Exception as e:
            logging.error(f"Error updating process info: {e}")

    def get_system_health(self) -> SystemHealthStatus:
        """Calculate overall system health based on multiple factors"""
        try:
            # Calculate health score (0-100)
            health_score = 100

            # CPU impact (0-30 points)
            cpu_impact = min(self.system_info['cpu_usage'] * 0.3, 30)
            health_score -= cpu_impact

            # Memory impact (0-30 points)
            memory_impact = min(self.system_info['memory_usage'] * 0.3, 30)
            health_score -= memory_impact

            # Disk impact (0-20 points)
            disk_impact = min(self.system_info['disk_usage'] * 0.2, 20)
            health_score -= disk_impact

            # Process count impact (0-20 points)
            process_impact = min((self.system_info['process_count'] / 200) * 20, 20)
            health_score -= process_impact

            # Determine health status
            if health_score >= 80:
                return SystemHealthStatus.EXCELLENT
            elif health_score >= 60:
                return SystemHealthStatus.GOOD
            elif health_score >= 40:
                return SystemHealthStatus.FAIR
            elif health_score >= 20:
                return SystemHealthStatus.POOR
            else:
                return SystemHealthStatus.CRITICAL

        except Exception as e:
            logging.error(f"Error calculating system health: {e}")
            return SystemHealthStatus.FAIR

class MonitoringWorker(QThread):
    """Background worker thread for system monitoring - collects data and emits signals"""
    data_ready = pyqtSignal(dict, dict)  # system_info, process_history
    
    def __init__(self, refresh_interval=2):
        super().__init__()
        self.refresh_interval = refresh_interval
        self.running = True
        self.system_monitor = SystemMonitor()
    
    def run(self):
        """Main worker loop - runs in background thread"""
        while self.running:
            try:
                # Collect data in background thread (this is the heavy work)
                self.system_monitor.update_system_info()
                
                # Emit signal with collected data (Qt handles thread-safe delivery)
                self.data_ready.emit(
                    self.system_monitor.system_info.copy(),
                    dict(self.system_monitor.process_history)
                )
                
                # Sleep in background thread
                self.msleep(int(self.refresh_interval * 1000))
                
            except Exception as e:
                logging.error(f"Error in monitoring worker: {e}")
                self.msleep(5000)
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.wait(5000)  # Wait up to 5 seconds for thread to finish
    
    def set_refresh_interval(self, interval):
        """Update the refresh interval"""
        self.refresh_interval = interval

class EnhancedGameMode:
    def __init__(self, ram_limit_mb: int = 500, whitelist: Optional[List[str]] = None):
        self.ram_limit_mb = ram_limit_mb
        self.whitelist = whitelist or []
        self.running = False
        self.thread = None
        self.performance_profile = PerformanceProfile.BALANCED
        self.aggressiveness = 5  # 1-10 scale
        self.system_monitor = SystemMonitor()
        self.notification_callback = None

        # Add default system processes to whitelist
        self._add_default_system_processes()

    def _add_default_system_processes(self):
        """Add critical system processes to whitelist"""
        system_processes = [
            'explorer.exe', 'system', 'systemd', 'svchost.exe',
            'csrss.exe', 'winlogon.exe', 'services.exe', 'lsass.exe',
            'smss.exe', 'wininit.exe', 'taskhost.exe', 'dwm.exe',
            'ctfmon.exe', 'runtimebroker.exe', 'sihost.exe',
            'fontdrvhost.exe', 'conhost.exe', 'nvvsvc.exe',
            'nvidia.exe', 'steam.exe', 'origin.exe', 'epicgameslauncher.exe',
            'ubisoftconnect.exe', 'battlenet.exe', 'eadesktop.exe'
        ]
        self.whitelist.extend([p.lower() for p in system_processes if p.lower() not in self.whitelist])

    def set_performance_profile(self, profile: PerformanceProfile):
        """Set performance profile which affects behavior"""
        self.performance_profile = profile

        # Adjust settings based on profile
        if profile == PerformanceProfile.GAMING:
            self.aggressiveness = 8
            self.ram_limit_mb = max(300, self.ram_limit_mb)  # Ensure reasonable minimum
        elif profile == PerformanceProfile.WORK:
            self.aggressiveness = 4
            self.ram_limit_mb = max(400, self.ram_limit_mb)
        elif profile == PerformanceProfile.BATTERY_SAVER:
            self.aggressiveness = 6
            self.ram_limit_mb = max(200, self.ram_limit_mb)
        else:  # Balanced
            self.aggressiveness = 5

    def start(self):
        """Start Game Mode in a separate thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        if self.notification_callback:
            self.notification_callback(
                f"Game Mode activated with {self.performance_profile.value} profile",
                NotificationType.SUCCESS
            )

    def stop(self):
        """Stop Game Mode"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

        if self.notification_callback:
            self.notification_callback(
                "Game Mode deactivated",
                NotificationType.INFO
            )

    def _run(self):
        """Main Game Mode loop"""
        while self.running:
            try:
                self.system_monitor.update_system_info()

                # Get current system health
                health_status = self.system_monitor.get_system_health()

                # Adjust behavior based on system health
                if health_status in [SystemHealthStatus.POOR, SystemHealthStatus.CRITICAL]:
                    # Be more aggressive when system is under stress
                    current_aggressiveness = min(self.aggressiveness + 3, 10)
                else:
                    current_aggressiveness = self.aggressiveness

                # Process management
                self._manage_processes(current_aggressiveness)

                # Sleep based on aggressiveness (more frequent checks when more aggressive)
                sleep_time = max(0.5, 3.0 - (current_aggressiveness * 0.25))
                time.sleep(sleep_time)

            except Exception as e:
                logging.error(f"Error in Game Mode: {e}")
                time.sleep(5)

    def _manage_processes(self, aggressiveness: int):
        """Manage processes based on current settings and system state"""
        try:
            # Get memory limit adjusted by aggressiveness
            effective_limit = self.ram_limit_mb * (0.8 + (aggressiveness * 0.02))

            terminated_count = 0

            for pid, proc_info in list(self.system_monitor.process_history.items()):
                try:
                    # Skip whitelisted processes
                    if proc_info.name.lower() in self.whitelist:
                        continue

                    # Skip system critical processes (extra safety)
                    if self._is_critical_process(proc_info.name):
                        continue

                    # Check if process exceeds memory limit
                    if proc_info.memory_usage > effective_limit:
                        try:
                            proc = psutil.Process(pid)
                            proc_name = proc.name()

                            # Additional safety checks
                            if self._can_safely_terminate(proc):
                                proc.terminate()
                                terminated_count += 1

                                if self.notification_callback:
                                    self.notification_callback(
                                        f"Terminated {proc_name} using {proc_info.memory_usage:.2f}MB "
                                        f"(Limit: {effective_limit:.2f}MB)",
                                        NotificationType.WARNING
                                    )
                                logging.info(f"Game Mode terminated {proc_name} (PID: {pid}) using {proc_info.memory_usage:.2f}MB")

                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                except Exception as e:
                    logging.error(f"Error managing process {pid}: {e}")
                    continue

            if terminated_count > 0 and self.notification_callback:
                self.notification_callback(
                    f"Game Mode terminated {terminated_count} processes exceeding memory limits",
                    NotificationType.INFO
                )

        except Exception as e:
            logging.error(f"Error in process management: {e}")

    def _is_critical_process(self, process_name: str) -> bool:
        """Check if process is critical and should never be terminated"""
        critical_processes = [
            'system', 'smss.exe', 'csrss.exe', 'wininit.exe',
            'services.exe', 'lsass.exe', 'svchost.exe', 'explorer.exe'
        ]
        return process_name.lower() in critical_processes

    def _can_safely_terminate(self, proc: psutil.Process) -> bool:
        """Additional safety checks before terminating a process"""
        try:
            # Don't terminate processes with high CPU usage (might be important)
            if proc.cpu_percent(interval=0.1) > 50:
                return False

            # Don't terminate processes that are children of critical processes
            parent = proc.parent()
            if parent and parent.name().lower() in self.whitelist:
                return False

            # Don't terminate processes with open windows
            if proc.name().lower().endswith('.exe') and self._process_has_windows(proc):
                return False

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _process_has_windows(self, proc: psutil.Process) -> bool:
        """Check if process has visible windows (Windows only)"""
        try:
            if platform.system() == 'Windows' and win32gui is not None and win32process is not None:

                def enum_windows_callback(hwnd, result):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid == proc.pid:
                        result.append(hwnd)
                    return True

                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                return len(windows) > 0
            return False
        except Exception:
            return False

class MemoryOptimizer:
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.process_priorities = {}
        self.memory_strategy = MemoryManagementStrategy.BALANCED
        self.optimization_mode = MemoryOptimizationMode.AUTOMATIC
        self.learning_data = {}
        self.notification_callback = None
        self.running = False
        self.thread = None

    def set_memory_strategy(self, strategy: MemoryManagementStrategy):
        self.memory_strategy = strategy

    def set_optimization_mode(self, mode: MemoryOptimizationMode):
        self.optimization_mode = mode

    def set_process_priority(self, process_name: str, priority: ProcessPriority):
        self.process_priorities[process_name.lower()] = priority

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.thread.start()

        if self.notification_callback:
            self.notification_callback(
                f"Memory optimizer started with {self.memory_strategy.name} strategy",
                NotificationType.SUCCESS
            )

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

        if self.notification_callback:
            self.notification_callback(
                "Memory optimizer stopped",
                NotificationType.INFO
            )

    def _optimization_loop(self):
        while self.running:
            try:
                self.system_monitor.update_system_info()
                self._apply_memory_optimization()
                time.sleep(2)  # Adjust based on system load

            except Exception as e:
                logging.error(f"Error in memory optimization loop: {e}")
                time.sleep(5)

    def _apply_memory_optimization(self):
        """Apply memory optimization based on current strategy and system state"""
        try:
            health_status = self.system_monitor.get_system_health()

            # Adjust strategy based on system health
            if health_status == SystemHealthStatus.CRITICAL:
                effective_strategy = MemoryManagementStrategy.AGGRESSIVE
            elif health_status == SystemHealthStatus.POOR:
                effective_strategy = MemoryManagementStrategy.AGGRESSIVE if self.memory_strategy != MemoryManagementStrategy.CONSERVATIVE else self.memory_strategy
            else:
                effective_strategy = self.memory_strategy

            # Apply optimization to processes
            for pid, proc_info in self.system_monitor.process_history.items():
                try:
                    proc = psutil.Process(pid)
                    self._optimize_process_memory(proc, proc_info, effective_strategy)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logging.error(f"Error applying memory optimization: {e}")

    def _optimize_process_memory(self, proc: psutil.Process, proc_info: ProcessInfo, strategy: MemoryManagementStrategy):
        """Optimize memory for a specific process"""
        try:
            process_name = proc.name().lower()
            priority = self.process_priorities.get(process_name, ProcessPriority.NORMAL)

            # Skip optimization for high priority processes
            if priority in [ProcessPriority.CRITICAL, ProcessPriority.HIGH]:
                return

            # Get memory limits based on strategy and priority
            memory_limit_percent = self._get_memory_limit_for_process(priority, strategy)

            if memory_limit_percent is None:
                return

            # Calculate target memory usage
            total_ram = psutil.virtual_memory().total
            max_memory = int(total_ram * (memory_limit_percent / 100))

            # Apply memory optimization
            self._limit_process_memory(proc, max_memory, strategy)

        except Exception as e:
            logging.error(f"Error optimizing memory for process {proc.pid}: {e}")

    def _get_memory_limit_for_process(self, priority: ProcessPriority, strategy: MemoryManagementStrategy) -> Optional[float]:
        """Get memory limit percentage based on process priority and optimization strategy"""
        if strategy == MemoryManagementStrategy.AGGRESSIVE:
            limits = {
                ProcessPriority.CRITICAL: None,  # No limit
                ProcessPriority.HIGH: 80,
                ProcessPriority.NORMAL: 50,
                ProcessPriority.LOW: 30,
                ProcessPriority.BACKGROUND: 20
            }
        elif strategy == MemoryManagementStrategy.BALANCED:
            limits = {
                ProcessPriority.CRITICAL: None,
                ProcessPriority.HIGH: 85,
                ProcessPriority.NORMAL: 60,
                ProcessPriority.LOW: 40,
                ProcessPriority.BACKGROUND: 25
            }
        else:  # CONSERVATIVE
            limits = {
                ProcessPriority.CRITICAL: None,
                ProcessPriority.HIGH: 90,
                ProcessPriority.NORMAL: 70,
                ProcessPriority.LOW: 50,
                ProcessPriority.BACKGROUND: 30
            }

        return limits.get(priority)

    def _limit_process_memory(self, proc: psutil.Process, max_memory: int, strategy: MemoryManagementStrategy):
        """Apply memory limits to a process using Windows API"""
        try:
            if platform.system() != 'Windows':
                return

            pid = proc.pid
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

            if not handle:
                return

            try:
                # Different approaches based on strategy
                if strategy == MemoryManagementStrategy.AGGRESSIVE:
                    # Empty working set first
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                    time.sleep(0.1)

                    # Set strict memory limit
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, 0, max_memory)

                    # Force garbage collection
                    for _ in range(3):
                        gc.collect()
                        time.sleep(0.1)

                elif strategy == MemoryManagementStrategy.BALANCED:
                    # More gentle approach
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, 0, max_memory)

                    # Single garbage collection
                    gc.collect()

                else:  # CONSERVATIVE
                    # Only set limit if process is using significantly more
                    current_memory = proc.memory_info().rss
                    if current_memory > max_memory * 1.5:  # 50% over limit
                        ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, 0, max_memory)
                        gc.collect()

            finally:
                ctypes.windll.kernel32.CloseHandle(handle)

        except Exception as e:
            logging.error(f"Error limiting memory for process {proc.pid}: {e}")

class ConfigurationManager:
    def __init__(self):
        self.current_config = {
            'version': '2.0',
            'profiles': {},
            'default_profile': 'balanced',
            'process_priorities': {},
            'game_mode_settings': {
                'ram_limit': 500,
                'whitelist': [],
                'performance_profile': 'balanced'
            },
            'notification_settings': {
                'enabled': True,
                'sound_enabled': False,
                'tray_notifications': True,
                'email_alerts': False,
                'sms_alerts': False
            },
            'ui_settings': {
                'theme': 'dark',
                'refresh_interval': 2,
                'show_advanced_stats': False
            },
            'advanced_settings': {
                'memory_strategy': 'balanced',
                'optimization_mode': 'automatic',
                'learning_enabled': True,
                'auto_start': False,
                'start_minimized': False
            }
        }
        self.config_file = 'ram_limiter_config.json'
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)

                # Merge with default config
                self._deep_update(self.current_config, loaded_config)
                self._migrate_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def _deep_update(self, original: dict, update: dict):
        """Recursively update dictionary"""
        for key, value in update.items():
            if isinstance(value, dict) and key in original:
                self._deep_update(original[key], value)
            else:
                original[key] = value

    def _migrate_config(self):
        """Migrate old config formats to new version"""
        if 'version' not in self.current_config:
            self.current_config['version'] = '1.0'

        # Add any missing keys from default config
        self._deep_update(self.current_config, {
            'version': '2.0',
            'profiles': self.current_config.get('profiles', {}),
            'default_profile': self.current_config.get('default_profile', 'balanced'),
            'process_priorities': self.current_config.get('process_priorities', {}),
            'game_mode_settings': self.current_config.get('game_mode_settings', {
                'ram_limit': 500,
                'whitelist': [],
                'performance_profile': 'balanced'
            }),
            'notification_settings': self.current_config.get('notification_settings', {
                'enabled': True,
                'sound_enabled': False,
                'tray_notifications': True,
                'email_alerts': False,
                'sms_alerts': False
            }),
            'ui_settings': self.current_config.get('ui_settings', {
                'theme': 'dark',
                'refresh_interval': 2,
                'show_advanced_stats': False
            }),
            'advanced_settings': self.current_config.get('advanced_settings', {
                'memory_strategy': 'balanced',
                'optimization_mode': 'automatic',
                'learning_enabled': True,
                'auto_start': False,
                'start_minimized': False
            })
        })

    def create_profile(self, profile_name: str, settings: dict):
        self.current_config['profiles'][profile_name] = settings
        self.save_config()

    def delete_profile(self, profile_name: str):
        if profile_name in self.current_config['profiles']:
            del self.current_config['profiles'][profile_name]
            self.save_config()

    def set_default_profile(self, profile_name: str):
        if profile_name in self.current_config['profiles']:
            self.current_config['default_profile'] = profile_name
            self.save_config()

class NotificationCenter:
    def __init__(self):
        self.notifications = deque(maxlen=100)
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def notify(self, message: str, notification_type: NotificationType = NotificationType.INFO):
        notification = {
            'timestamp': datetime.now(),
            'message': message,
            'type': notification_type.name,
            'read': False
        }
        self.notifications.append(notification)

        # Call all registered callbacks
        for callback in self.callbacks:
            try:
                callback(message, notification_type)
            except Exception as e:
                logging.error(f"Error in notification callback: {e}")

    def get_unread_notifications(self) -> List[dict]:
        return [n for n in self.notifications if not n['read']]

    def mark_all_as_read(self):
        for notification in self.notifications:
            notification['read'] = True

class EnhancedRAMLimiterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RAM Limiter Enhanced')
        self.setMinimumSize(1000, 800)

        # Initialize components
        self.system_monitor = SystemMonitor()
        self.memory_optimizer = MemoryOptimizer()
        self.game_mode = EnhancedGameMode()
        self.config_manager = ConfigurationManager()
        self.notification_center = NotificationCenter()

        # Connect notification system
        self.memory_optimizer.notification_callback = self.handle_notification
        self.game_mode.notification_callback = self.handle_notification
        self.notification_center.register_callback(self.show_notification)

        # Setup UI
        self.init_ui()
        self.load_settings()

        # Start monitoring using background worker thread with signals
        # Worker collects data in background, emits signal to update UI on main thread
        refresh_interval = self.config_manager.current_config['ui_settings']['refresh_interval']
        self.monitoring_worker = MonitoringWorker(refresh_interval)
        self.monitoring_worker.data_ready.connect(self.on_monitoring_data)
        self.monitoring_worker.start()
        
        # Store current data for UI access
        self.current_system_info = {}
        self.current_process_history = {}

        # Setup tray icon
        self.setup_tray_icon()

        # Start auto-optimization if enabled
        if self.config_manager.current_config['advanced_settings']['auto_start']:
            self.start_auto_optimization()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create tab widget for different sections
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px;
                background: #3c3c3c;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                border-bottom: none;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #2ecc71;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #4a4a4a;
            }
        """)

        # Create tabs
        self.dashboard_tab = self.create_dashboard_tab()
        self.process_manager_tab = self.create_process_manager_tab()
        self.game_mode_tab = self.create_game_mode_tab()
        self.settings_tab = self.create_settings_tab()
        self.notifications_tab = self.create_notifications_tab()
        self.analytics_tab = self.create_analytics_tab()

        self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tab_widget.addTab(self.process_manager_tab, "🔧 Process Manager")
        self.tab_widget.addTab(self.game_mode_tab, "🎮 Game Mode")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        self.tab_widget.addTab(self.notifications_tab, "🔔 Notifications")
        self.tab_widget.addTab(self.analytics_tab, "📈 Analytics")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def create_dashboard_tab(self):
        """Create the dashboard tab with system overview"""
        dashboard = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # System health indicator
        self.health_indicator = QLabel()
        self.health_indicator.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                background: #3c3c3c;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.health_indicator)

        # System stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        # CPU Stats
        cpu_group = QGroupBox("CPU")
        cpu_layout = QVBoxLayout()
        self.cpu_usage_label = QLabel("0%")
        self.cpu_usage_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.cpu_freq_label = QLabel("0 GHz")
        self.cpu_cores_label = QLabel("0 cores")
        cpu_layout.addWidget(self.cpu_usage_label)
        cpu_layout.addWidget(self.cpu_freq_label)
        cpu_layout.addWidget(self.cpu_cores_label)
        cpu_group.setLayout(cpu_layout)
        stats_grid.addWidget(cpu_group, 0, 0)

        # Memory Stats
        memory_group = QGroupBox("Memory")
        memory_layout = QVBoxLayout()
        self.memory_usage_label = QLabel("0%")
        self.memory_usage_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.memory_used_label = QLabel("0/0 MB")
        self.memory_available_label = QLabel("0 MB available")
        memory_layout.addWidget(self.memory_usage_label)
        memory_layout.addWidget(self.memory_used_label)
        memory_layout.addWidget(self.memory_available_label)
        memory_group.setLayout(memory_layout)
        stats_grid.addWidget(memory_group, 0, 1)

        # Disk Stats
        disk_group = QGroupBox("Disk")
        disk_layout = QVBoxLayout()
        self.disk_usage_label = QLabel("0%")
        self.disk_usage_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.disk_used_label = QLabel("0/0 GB")
        self.disk_free_label = QLabel("0 GB free")
        disk_layout.addWidget(self.disk_usage_label)
        disk_layout.addWidget(self.disk_used_label)
        disk_layout.addWidget(self.disk_free_label)
        disk_group.setLayout(disk_layout)
        stats_grid.addWidget(disk_group, 0, 2)

        # Network Stats
        network_group = QGroupBox("Network")
        network_layout = QVBoxLayout()
        self.network_sent_label = QLabel("0 MB sent")
        self.network_received_label = QLabel("0 MB received")
        self.network_total_label = QLabel("0 MB total")
        network_layout.addWidget(self.network_sent_label)
        network_layout.addWidget(self.network_received_label)
        network_layout.addWidget(self.network_total_label)
        network_group.setLayout(network_layout)
        stats_grid.addWidget(network_group, 0, 3)

        layout.addLayout(stats_grid)

        # System load chart
        self.load_chart = pg.PlotWidget()
        self.load_chart.setBackground('#2b2b2b')
        self.load_chart.setTitle("System Load Over Time", color='#00b4d8')
        self.load_chart.setLabel('left', 'Usage (%)', color='#ffffff')
        self.load_chart.setLabel('bottom', 'Time', color='#ffffff')
        self.load_chart.showGrid(x=True, y=True, alpha=0.3)

        # Multiple curves for different metrics
        self.cpu_curve = self.load_chart.plot(pen=pg.mkPen('#3498db', width=2), name="CPU")
        self.memory_curve = self.load_chart.plot(pen=pg.mkPen('#e74c3c', width=2), name="Memory")
        self.disk_curve = self.load_chart.plot(pen=pg.mkPen('#2ecc71', width=2), name="Disk")

        # Store data for charts
        self.chart_data = {
            'cpu': deque(maxlen=100),
            'memory': deque(maxlen=100),
            'disk': deque(maxlen=100),
            'timestamps': deque(maxlen=100)
        }

        layout.addWidget(self.load_chart)

        # Quick actions
        actions_layout = QHBoxLayout()
        self.optimize_now_btn = QPushButton("⚡ Optimize Now")
        self.optimize_now_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #2ecc71);
            }
        """)
        self.optimize_now_btn.clicked.connect(self.optimize_now)

        self.toggle_auto_btn = QPushButton("🤖 Auto Optimization: OFF")
        self.toggle_auto_btn.setCheckable(True)
        self.toggle_auto_btn.setStyleSheet("""
            QPushButton {
                background: #3c3c3c;
                color: #ffffff;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
        """)
        self.toggle_auto_btn.clicked.connect(self.toggle_auto_optimization)

        actions_layout.addWidget(self.optimize_now_btn)
        actions_layout.addWidget(self.toggle_auto_btn)
        layout.addLayout(actions_layout)

        # Process list
        process_group = QGroupBox("Top Memory Processes")
        process_layout = QVBoxLayout()

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["Process", "PID", "Memory (MB)", "CPU (%)", "Priority"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setStyleSheet("""
            QTableWidget {
                background: #353535;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                gridline-color: #4a4a4a;
            }
            QHeaderView::section {
                background: #3c3c3c;
                color: #00b4d8;
                padding: 5px;
                border: none;
            }
        """)
        self.process_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        process_layout.addWidget(self.process_table)
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        dashboard.setLayout(layout)
        return dashboard

    def create_process_manager_tab(self):
        """Create the process manager tab"""
        process_manager = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Process control group
        control_group = QGroupBox("Process Control")
        control_layout = QVBoxLayout()

        # Process selection
        process_layout = QHBoxLayout()
        self.process_combo = QComboBox()
        self.process_combo.setMinimumWidth(200)
        self.refresh_process_btn = QPushButton("🔄 Refresh")
        self.refresh_process_btn.clicked.connect(self.refresh_process_list)

        process_layout.addWidget(QLabel("Select Process:"))
        process_layout.addWidget(self.process_combo)
        process_layout.addWidget(self.refresh_process_btn)
        control_layout.addLayout(process_layout)

        # Priority settings
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Critical", "High", "Normal", "Low", "Background"])
        self.priority_combo.currentIndexChanged.connect(self.update_process_priority)

        priority_layout.addWidget(self.priority_combo)
        control_layout.addLayout(priority_layout)

        # Memory limit settings
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Memory Limit (%):"))
        self.memory_limit_slider = QSlider(Qt.Horizontal)
        self.memory_limit_slider.setRange(10, 90)
        self.memory_limit_slider.setValue(60)
        self.memory_limit_label = QLabel("60%")
        self.memory_limit_slider.valueChanged.connect(self.update_memory_limit_label)

        limit_layout.addWidget(self.memory_limit_slider)
        limit_layout.addWidget(self.memory_limit_label)
        control_layout.addLayout(limit_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        self.limit_process_btn = QPushButton("📉 Limit Memory")
        self.limit_process_btn.clicked.connect(self.limit_selected_process)

        self.terminate_process_btn = QPushButton("❌ Terminate")
        self.terminate_process_btn.setStyleSheet("background: #e74c3c; color: white;")
        self.terminate_process_btn.clicked.connect(self.terminate_selected_process)

        action_layout.addWidget(self.limit_process_btn)
        action_layout.addWidget(self.terminate_process_btn)
        control_layout.addLayout(action_layout)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Advanced process list
        advanced_process_group = QGroupBox("Advanced Process Management")
        advanced_layout = QVBoxLayout()

        self.advanced_process_table = QTableWidget()
        self.advanced_process_table.setColumnCount(8)
        self.advanced_process_table.setHorizontalHeaderLabels([
            "Process", "PID", "Memory (MB)", "CPU (%)",
            "Threads", "Handles", "Priority", "Actions"
        ])
        self.advanced_process_table.horizontalHeader().setStretchLastSection(True)
        self.advanced_process_table.setStyleSheet("""
            QTableWidget {
                background: #353535;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                gridline-color: #4a4a4a;
            }
            QHeaderView::section {
                background: #3c3c3c;
                color: #00b4d8;
                padding: 5px;
                border: none;
            }
        """)

        advanced_layout.addWidget(self.advanced_process_table)
        advanced_process_group.setLayout(advanced_layout)
        layout.addWidget(advanced_process_group)

        process_manager.setLayout(layout)
        return process_manager

    def create_game_mode_tab(self):
        """Create the enhanced Game Mode tab"""
        game_mode_tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Game Mode control
        game_control_group = QGroupBox("Game Mode Control")
        game_control_layout = QVBoxLayout()

        # Enable toggle
        self.game_mode_toggle = QPushButton("🎮 Enable Game Mode")
        self.game_mode_toggle.setCheckable(True)
        self.game_mode_toggle.setStyleSheet("""
            QPushButton {
                background: #3c3c3c;
                color: #ffffff;
                padding: 15px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                font-weight: bold;
            }
        """)
        self.game_mode_toggle.clicked.connect(self.toggle_game_mode)

        # Performance profile
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Performance Profile:"))
        self.game_profile_combo = QComboBox()
        self.game_profile_combo.addItems(["Balanced", "Gaming", "Work", "Battery Saver"])
        self.game_profile_combo.currentIndexChanged.connect(self.update_game_profile)

        profile_layout.addWidget(self.game_profile_combo)
        game_control_layout.addLayout(profile_layout)

        # RAM limit
        ram_layout = QHBoxLayout()
        ram_layout.addWidget(QLabel("RAM Limit (MB):"))
        self.game_ram_limit_spin = QSpinBox()
        self.game_ram_limit_spin.setRange(100, 4096)
        self.game_ram_limit_spin.setValue(500)

        ram_layout.addWidget(self.game_ram_limit_spin)
        game_control_layout.addLayout(ram_layout)

        # Aggressiveness slider
        aggressiveness_layout = QHBoxLayout()
        aggressiveness_layout.addWidget(QLabel("Aggressiveness:"))
        self.aggressiveness_slider = QSlider(Qt.Horizontal)
        self.aggressiveness_slider.setRange(1, 10)
        self.aggressiveness_slider.setValue(5)
        self.aggressiveness_label = QLabel("5")

        aggressiveness_layout.addWidget(self.aggressiveness_slider)
        aggressiveness_layout.addWidget(self.aggressiveness_label)
        game_control_layout.addLayout(aggressiveness_layout)

        game_control_layout.addWidget(self.game_mode_toggle)
        game_control_group.setLayout(game_control_layout)
        layout.addWidget(game_control_group)

        # Whitelist management
        whitelist_group = QGroupBox("Process Whitelist")
        whitelist_layout = QVBoxLayout()

        self.whitelist_edit = QLineEdit()
        self.whitelist_edit.setPlaceholderText("Enter processes to whitelist (comma-separated)")
        self.whitelist_list = QListWidget()
        self.whitelist_list.setStyleSheet("""
            QListWidget {
                background: #353535;
                color: #ffffff;
                border: 1px solid #4a4a4a;
            }
        """)

        whitelist_button_layout = QHBoxLayout()
        self.add_whitelist_btn = QPushButton("➕ Add")
        self.add_whitelist_btn.clicked.connect(self.add_to_whitelist)

        self.remove_whitelist_btn = QPushButton("➖ Remove")
        self.remove_whitelist_btn.clicked.connect(self.remove_from_whitelist)

        whitelist_button_layout.addWidget(self.add_whitelist_btn)
        whitelist_button_layout.addWidget(self.remove_whitelist_btn)

        whitelist_layout.addWidget(self.whitelist_edit)
        whitelist_layout.addLayout(whitelist_button_layout)
        whitelist_layout.addWidget(self.whitelist_list)
        whitelist_group.setLayout(whitelist_layout)
        layout.addWidget(whitelist_group)

        # Game Mode status
        status_group = QGroupBox("Game Mode Status")
        status_layout = QVBoxLayout()

        self.game_mode_status = QLabel("Game Mode: Disabled")
        self.game_mode_status.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.terminated_processes_label = QLabel("Processes terminated: 0")
        self.memory_freed_label = QLabel("Memory freed: 0 MB")

        status_layout.addWidget(self.game_mode_status)
        status_layout.addWidget(self.terminated_processes_label)
        status_layout.addWidget(self.memory_freed_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        game_mode_tab.setLayout(layout)
        return game_mode_tab

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Create tab widget for different setting categories
        settings_tab_widget = QTabWidget()

        # General settings
        general_settings = QWidget()
        general_layout = QFormLayout()

        self.auto_start_checkbox = QCheckBox("Auto-start optimization on launch")
        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])

        general_layout.addRow("Auto Start:", self.auto_start_checkbox)
        general_layout.addRow("Start Minimized:", self.start_minimized_checkbox)
        general_layout.addRow("Theme:", self.theme_combo)
        general_settings.setLayout(general_layout)

        # Memory settings
        memory_settings = QWidget()
        memory_layout = QFormLayout()

        self.memory_strategy_combo = QComboBox()
        self.memory_strategy_combo.addItems(["Balanced", "Aggressive", "Conservative"])

        self.optimization_mode_combo = QComboBox()
        self.optimization_mode_combo.addItems(["Automatic", "Manual", "Learning"])

        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 10)
        self.refresh_interval_spin.setValue(2)

        memory_layout.addRow("Memory Strategy:", self.memory_strategy_combo)
        memory_layout.addRow("Optimization Mode:", self.optimization_mode_combo)
        memory_layout.addRow("Refresh Interval (s):", self.refresh_interval_spin)
        memory_settings.setLayout(memory_layout)

        # Notification settings
        notification_settings = QWidget()
        notification_layout = QFormLayout()

        self.enable_notifications_checkbox = QCheckBox("Enable notifications")
        self.tray_notifications_checkbox = QCheckBox("Show tray notifications")
        self.sound_notifications_checkbox = QCheckBox("Play notification sounds")

        notification_layout.addRow(self.enable_notifications_checkbox)
        notification_layout.addRow(self.tray_notifications_checkbox)
        notification_layout.addRow(self.sound_notifications_checkbox)
        notification_settings.setLayout(notification_layout)

        # Profile management
        profile_settings = QWidget()
        profile_layout = QVBoxLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Default", "Gaming", "Work", "Battery Saver"])

        profile_button_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton("💾 Save Profile")
        self.delete_profile_btn = QPushButton("🗑️ Delete Profile")
        self.export_profile_btn = QPushButton("📤 Export Profile")
        self.import_profile_btn = QPushButton("📥 Import Profile")

        profile_button_layout.addWidget(self.save_profile_btn)
        profile_button_layout.addWidget(self.delete_profile_btn)
        profile_button_layout.addWidget(self.export_profile_btn)
        profile_button_layout.addWidget(self.import_profile_btn)

        profile_layout.addWidget(QLabel("Current Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addLayout(profile_button_layout)
        profile_settings.setLayout(profile_layout)

        settings_tab_widget.addTab(general_settings, "General")
        settings_tab_widget.addTab(memory_settings, "Memory")
        settings_tab_widget.addTab(notification_settings, "Notifications")
        settings_tab_widget.addTab(profile_settings, "Profiles")

        layout.addWidget(settings_tab_widget)

        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        settings_tab.setLayout(layout)
        return settings_tab

    def create_notifications_tab(self):
        """Create the notifications tab"""
        notifications_tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Notification list
        self.notification_list = QListWidget()
        self.notification_list.setStyleSheet("""
            QListWidget {
                background: #353535;
                color: #ffffff;
                border: 1px solid #4a4a4a;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a4a4a;
            }
        """)

        # Notification controls
        control_layout = QHBoxLayout()
        self.clear_notifications_btn = QPushButton("🗑️ Clear All")
        self.clear_notifications_btn.clicked.connect(self.clear_notifications)

        self.mark_read_btn = QPushButton("✓ Mark All Read")
        self.mark_read_btn.clicked.connect(self.mark_all_notifications_read)

        control_layout.addWidget(self.clear_notifications_btn)
        control_layout.addWidget(self.mark_read_btn)

        layout.addWidget(self.notification_list)
        layout.addLayout(control_layout)

        notifications_tab.setLayout(layout)
        return notifications_tab

    def create_analytics_tab(self):
        """Create the analytics tab"""
        analytics_tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # System health history chart
        self.health_chart = pg.PlotWidget()
        self.health_chart.setBackground('#2b2b2b')
        self.health_chart.setTitle("System Health Over Time", color='#00b4d8')
        self.health_chart.setLabel('left', 'Health Score', color='#ffffff')
        self.health_chart.setLabel('bottom', 'Time', color='#ffffff')
        self.health_chart.showGrid(x=True, y=True, alpha=0.3)

        self.health_curve = self.health_chart.plot(pen=pg.mkPen('#9b59b6', width=2), name="Health Score")

        # Memory usage history
        self.memory_history_chart = pg.PlotWidget()
        self.memory_history_chart.setBackground('#2b2b2b')
        self.memory_history_chart.setTitle("Memory Usage History", color='#00b4d8')
        self.memory_history_chart.setLabel('left', 'Memory (MB)', color='#ffffff')
        self.memory_history_chart.setLabel('bottom', 'Time', color='#ffffff')
        self.memory_history_chart.showGrid(x=True, y=True, alpha=0.3)

        self.memory_history_curve = self.memory_history_chart.plot(pen=pg.mkPen('#e74c3c', width=2), name="Memory Usage")

        # Add charts to layout
        layout.addWidget(self.health_chart)
        layout.addWidget(self.memory_history_chart)

        # Statistics
        stats_group = QGroupBox("System Statistics")
        stats_layout = QGridLayout()

        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.peak_memory_label = QLabel("Peak Memory: 0 MB")
        self.avg_cpu_label = QLabel("Avg CPU: 0%")
        self.total_optimizations_label = QLabel("Optimizations: 0")

        stats_layout.addWidget(self.uptime_label, 0, 0)
        stats_layout.addWidget(self.peak_memory_label, 0, 1)
        stats_layout.addWidget(self.avg_cpu_label, 1, 0)
        stats_layout.addWidget(self.total_optimizations_label, 1, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Export button
        export_btn = QPushButton("📊 Export Analytics Data")
        export_btn.clicked.connect(self.export_analytics)
        layout.addWidget(export_btn)

        analytics_tab.setLayout(layout)
        return analytics_tab

    def on_monitoring_data(self, system_info, process_history):
        """Handle monitoring data received from background worker (runs on main thread)"""
        try:
            # Store the data for use by update methods
            self.current_system_info = system_info
            self.current_process_history = process_history
            
            # Also update the system_monitor's data for compatibility
            self.system_monitor.system_info = system_info
            self.system_monitor.process_history = process_history

            # Update dashboard (safe - runs on main thread)
            self.update_dashboard()

            # Update process tables
            self.update_process_tables()

            # Update charts
            self.update_charts()

            # Check for notifications
            self.check_system_alerts()

            # Update worker interval if refresh rate changed
            refresh_interval = self.config_manager.current_config['ui_settings']['refresh_interval']
            if hasattr(self, 'monitoring_worker'):
                self.monitoring_worker.set_refresh_interval(refresh_interval)

        except Exception as e:
            logging.error(f"Error in monitoring data handler: {e}")

    def update_dashboard(self):
        """Update dashboard with current system information"""
        try:
            system_info = self.system_monitor.system_info

            # Update health indicator
            health_status = self.system_monitor.get_system_health()
            health_colors = {
                SystemHealthStatus.EXCELLENT: "#2ecc71",
                SystemHealthStatus.GOOD: "#27ae60",
                SystemHealthStatus.FAIR: "#f39c12",
                SystemHealthStatus.POOR: "#e67e22",
                SystemHealthStatus.CRITICAL: "#e74c3c"
            }
            color = health_colors.get(health_status, "#95a5a6")
            self.health_indicator.setText(f"🏥 System Health: {health_status.value}")
            self.health_indicator.setStyleSheet(f"""
                QLabel {{
                    font-size: 24px;
                    font-weight: bold;
                    padding: 15px;
                    border-radius: 10px;
                    background: {color};
                    color: {'#ffffff' if color not in ['#2ecc71', '#27ae60'] else '#000000'};
                }}
            """)

            # Update CPU stats
            self.cpu_usage_label.setText(f"{system_info['cpu_usage']:.1f}%")
            if system_info['cpu_frequency']:
                self.cpu_freq_label.setText(f"{system_info['cpu_frequency']['current'] / 1000:.2f} GHz")
            self.cpu_cores_label.setText(f"{system_info['cpu_cores']} cores")

            # Update memory stats
            self.memory_usage_label.setText(f"{system_info['memory_usage']:.1f}%")
            self.memory_used_label.setText(f"{system_info['memory_used'] / (1024 * 1024):.1f} / {system_info['memory_total'] / (1024 * 1024):.1f} GB")
            self.memory_available_label.setText(f"{system_info['memory_available'] / (1024 * 1024):.1f} GB available")

            # Update disk stats
            self.disk_usage_label.setText(f"{system_info['disk_usage']:.1f}%")
            self.disk_used_label.setText(f"{system_info['disk_used'] / (1024 * 1024 * 1024):.1f} / {system_info['disk_total'] / (1024 * 1024 * 1024):.1f} GB")
            self.disk_free_label.setText(f"{system_info['disk_free'] / (1024 * 1024 * 1024):.1f} GB free")

            # Update network stats
            self.network_sent_label.setText(f"{system_info['network_sent'] / (1024 * 1024):.2f} MB sent")
            self.network_received_label.setText(f"{system_info['network_received'] / (1024 * 1024):.2f} MB received")
            total_network = (system_info['network_sent'] + system_info['network_received']) / (1024 * 1024)
            self.network_total_label.setText(f"{total_network:.2f} MB total")

        except Exception as e:
            logging.error(f"Error updating dashboard: {e}")

    def update_process_tables(self):
        """Update process tables with current process information"""
        try:
            # Update main process table (top processes)
            self.process_table.setRowCount(0)

            # Sort processes by memory usage
            sorted_processes = sorted(
                self.system_monitor.process_history.values(),
                key=lambda p: p.memory_usage,
                reverse=True
            )[:10]  # Top 10 processes

            for row, proc_info in enumerate(sorted_processes):
                self.process_table.insertRow(row)

                # Process name
                name_item = QTableWidgetItem(proc_info.name)
                name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                # PID
                pid_item = QTableWidgetItem(str(proc_info.pid))
                pid_item.setTextAlignment(Qt.AlignCenter)

                # Memory usage
                memory_item = QTableWidgetItem(f"{proc_info.memory_usage:.1f}")
                memory_item.setTextAlignment(Qt.AlignRight)

                # CPU usage
                cpu_item = QTableWidgetItem(f"{proc_info.cpu_usage:.1f}")
                cpu_item.setTextAlignment(Qt.AlignRight)

                # Priority
                priority_item = QTableWidgetItem(proc_info.priority.name.capitalize())
                priority_item.setTextAlignment(Qt.AlignCenter)

                self.process_table.setItem(row, 0, name_item)
                self.process_table.setItem(row, 1, pid_item)
                self.process_table.setItem(row, 2, memory_item)
                self.process_table.setItem(row, 3, cpu_item)
                self.process_table.setItem(row, 4, priority_item)

            # Update advanced process table
            self.advanced_process_table.setRowCount(0)

            for row, proc_info in enumerate(self.system_monitor.process_history.values()):
                self.advanced_process_table.insertRow(row)

                # Process name
                name_item = QTableWidgetItem(proc_info.name)

                # PID
                pid_item = QTableWidgetItem(str(proc_info.pid))
                pid_item.setTextAlignment(Qt.AlignCenter)

                # Memory usage
                memory_item = QTableWidgetItem(f"{proc_info.memory_usage:.1f}")
                memory_item.setTextAlignment(Qt.AlignRight)

                # CPU usage
                cpu_item = QTableWidgetItem(f"{proc_info.cpu_usage:.1f}")
                cpu_item.setTextAlignment(Qt.AlignRight)

                # Threads and Handles (placeholder for now)
                threads_item = QTableWidgetItem("N/A")
                handles_item = QTableWidgetItem("N/A")

                # Priority
                priority_item = QTableWidgetItem(proc_info.priority.name.capitalize())

                # Actions button
                actions_btn = QPushButton("⚙️")
                actions_btn.setProperty("pid", proc_info.pid)
                actions_btn.clicked.connect(self.show_process_actions)

                self.advanced_process_table.setItem(row, 0, name_item)
                self.advanced_process_table.setItem(row, 1, pid_item)
                self.advanced_process_table.setItem(row, 2, memory_item)
                self.advanced_process_table.setItem(row, 3, cpu_item)
                self.advanced_process_table.setItem(row, 4, threads_item)
                self.advanced_process_table.setItem(row, 5, handles_item)
                self.advanced_process_table.setItem(row, 6, priority_item)
                self.advanced_process_table.setCellWidget(row, 7, actions_btn)

        except Exception as e:
            logging.error(f"Error updating process tables: {e}")

    def update_charts(self):
        """Update all charts with current data"""
        try:
            system_info = self.system_monitor.system_info
            current_time = time.time()

            # Update main load chart
            self.chart_data['cpu'].append(system_info['cpu_usage'])
            self.chart_data['memory'].append(system_info['memory_usage'])
            self.chart_data['disk'].append(system_info['disk_usage'])
            self.chart_data['timestamps'].append(current_time)

            # Update curves
            if len(self.chart_data['timestamps']) > 1:
                # Convert timestamps to relative time for x-axis
                start_time = self.chart_data['timestamps'][0]
                x_data = [t - start_time for t in self.chart_data['timestamps']]

                self.cpu_curve.setData(x_data, list(self.chart_data['cpu']))
                self.memory_curve.setData(x_data, list(self.chart_data['memory']))
                self.disk_curve.setData(x_data, list(self.chart_data['disk']))

                # Auto-range the view
                self.load_chart.setXRange(0, max(x_data))
                self.load_chart.setYRange(0, 100)

            # Update analytics charts
            self.update_analytics_charts()

        except Exception as e:
            logging.error(f"Error updating charts: {e}")

    def update_analytics_charts(self):
        """Update analytics charts"""
        try:
            # Health score calculation
            health_status = self.system_monitor.get_system_health()
            health_scores = {
                SystemHealthStatus.EXCELLENT: 100,
                SystemHealthStatus.GOOD: 75,
                SystemHealthStatus.FAIR: 50,
                SystemHealthStatus.POOR: 25,
                SystemHealthStatus.CRITICAL: 10
            }
            health_score = health_scores.get(health_status, 50)

            # Add health score to chart
            current_time = time.time()
            if not hasattr(self, 'health_timestamps'):
                self.health_timestamps = deque(maxlen=100)
                self.health_scores = deque(maxlen=100)

            self.health_timestamps.append(current_time)
            self.health_scores.append(health_score)

            if len(self.health_timestamps) > 1:
                start_time = self.health_timestamps[0]
                x_data = [t - start_time for t in self.health_timestamps]
                self.health_curve.setData(x_data, list(self.health_scores))
                self.health_chart.setXRange(0, max(x_data))
                self.health_chart.setYRange(0, 100)

            # Memory usage history
            memory_usage_mb = self.system_monitor.system_info['memory_used'] / (1024 * 1024)
            if not hasattr(self, 'memory_timestamps'):
                self.memory_timestamps = deque(maxlen=100)
                self.memory_usages = deque(maxlen=100)

            self.memory_timestamps.append(current_time)
            self.memory_usages.append(memory_usage_mb)

            if len(self.memory_timestamps) > 1:
                start_time = self.memory_timestamps[0]
                x_data = [t - start_time for t in self.memory_timestamps]
                self.memory_history_curve.setData(x_data, list(self.memory_usages))
                self.memory_history_chart.setXRange(0, max(x_data))
                max_memory = max(self.memory_usages) * 1.1 if self.memory_usages else 1000
                self.memory_history_chart.setYRange(0, max_memory)

        except Exception as e:
            logging.error(f"Error updating analytics charts: {e}")

    def check_system_alerts(self):
        """Check for system conditions that require notifications"""
        try:
            system_info = self.system_monitor.system_info
            health_status = self.system_monitor.get_system_health()

            # High CPU alert
            if system_info['cpu_usage'] > 90:
                self.notification_center.notify(
                    f"⚠️ High CPU usage: {system_info['cpu_usage']:.1f}%",
                    NotificationType.WARNING
                )

            # High memory alert
            if system_info['memory_usage'] > 90:
                self.notification_center.notify(
                    f"⚠️ High memory usage: {system_info['memory_usage']:.1f}%",
                    NotificationType.WARNING
                )

            # Critical health alert
            if health_status == SystemHealthStatus.CRITICAL:
                self.notification_center.notify(
                    "🚨 System health critical! Immediate action recommended.",
                    NotificationType.ERROR
                )

            # Process count alert
            if system_info['process_count'] > 200:
                self.notification_center.notify(
                    f"📈 High process count: {system_info['process_count']} processes running",
                    NotificationType.WARNING
                )

        except Exception as e:
            logging.error(f"Error checking system alerts: {e}")

    def handle_notification(self, message: str, notification_type: NotificationType):
        """Handle notifications from various components"""
        self.notification_center.notify(message, notification_type)

    def show_notification(self, message: str, notification_type: NotificationType):
        """Display notification in the UI"""
        try:
            # Add to notification list
            notification_item = QListWidgetItem()
            notification_item.setText(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

            # Set color based on type
            colors = {
                NotificationType.INFO: "#3498db",
                NotificationType.WARNING: "#f39c12",
                NotificationType.ERROR: "#e74c3c",
                NotificationType.SUCCESS: "#2ecc71"
            }
            color = colors.get(notification_type, "#95a5a6")

            notification_item.setForeground(QColor(color))

            # Add to top of list
            self.notification_list.insertItem(0, notification_item)

            # Show tray notification if enabled
            if self.config_manager.current_config['notification_settings']['tray_notifications']:
                self.tray_icon.showMessage(
                    "RAM Limiter",
                    message,
                    QSystemTrayIcon.Information,
                    3000
                )

        except Exception as e:
            logging.error(f"Error showing notification: {e}")

    def clear_notifications(self):
        """Clear all notifications"""
        self.notification_list.clear()
        self.notification_center.mark_all_as_read()

    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        self.notification_center.mark_all_as_read()
        for i in range(self.notification_list.count()):
            item = self.notification_list.item(i)
            item.setForeground(QColor("#95a5a6"))

    def refresh_process_list(self):
        """Refresh the process list in the combo box"""
        try:
            self.process_combo.clear()
            process_names = sorted(set(p.name for p in self.system_monitor.process_history.values()))
            self.process_combo.addItems(process_names)
        except Exception as e:
            logging.error(f"Error refreshing process list: {e}")

    def update_process_priority(self):
        """Update priority for selected process"""
        try:
            process_name = self.process_combo.currentText()
            if not process_name:
                return

            priority_index = self.priority_combo.currentIndex()
            priorities = [ProcessPriority.CRITICAL, ProcessPriority.HIGH,
                         ProcessPriority.NORMAL, ProcessPriority.LOW,
                         ProcessPriority.BACKGROUND]
            priority = priorities[priority_index]

            self.memory_optimizer.set_process_priority(process_name, priority)
            self.notification_center.notify(
                f"Set {process_name} priority to {priority.name}",
                NotificationType.INFO
            )

        except Exception as e:
            logging.error(f"Error updating process priority: {e}")

    def update_memory_limit_label(self, value: int):
        """Update memory limit label"""
        self.memory_limit_label.setText(f"{value}%")

    def limit_selected_process(self):
        """Limit memory for selected process"""
        try:
            process_name = self.process_combo.currentText()
            if not process_name:
                QMessageBox.warning(self, "Error", "Please select a process")
                return

            memory_limit = self.memory_limit_slider.value()
            self.memory_optimizer.set_process_priority(process_name, ProcessPriority.LOW)

            # Find and limit the process
            for pid, proc_info in self.system_monitor.process_history.items():
                if proc_info.name == process_name:
                    try:
                        proc = psutil.Process(pid)
                        total_ram = psutil.virtual_memory().total
                        max_memory = int(total_ram * (memory_limit / 100))

                        # Apply memory limit
                        if platform.system() == 'Windows':
                            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                            if handle:
                                try:
                                    ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, 0, max_memory)
                                    gc.collect()
                                finally:
                                    ctypes.windll.kernel32.CloseHandle(handle)

                        self.notification_center.notify(
                            f"Limited {process_name} to {memory_limit}% of total RAM",
                            NotificationType.SUCCESS
                        )
                        break

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        except Exception as e:
            logging.error(f"Error limiting process: {e}")
            QMessageBox.critical(self, "Error", f"Failed to limit process: {str(e)}")

    def terminate_selected_process(self):
        """Terminate selected process"""
        try:
            process_name = self.process_combo.currentText()
            if not process_name:
                QMessageBox.warning(self, "Error", "Please select a process")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self, "Confirm Termination",
                f"Are you sure you want to terminate {process_name}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

            # Terminate the process
            for pid, proc_info in list(self.system_monitor.process_history.items()):
                if proc_info.name == process_name:
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()

                        self.notification_center.notify(
                            f"Terminated {process_name} (PID: {pid})",
                            NotificationType.WARNING
                        )
                        return

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            QMessageBox.warning(self, "Error", f"Could not terminate {process_name}")

        except Exception as e:
            logging.error(f"Error terminating process: {e}")
            QMessageBox.critical(self, "Error", f"Failed to terminate process: {str(e)}")

    def show_process_actions(self):
        """Show actions menu for a process"""
        try:
            button = self.sender()
            if not button:
                return

            pid = button.property("pid")
            if not pid:
                return

            # Find the process
            proc_info = self.system_monitor.process_history.get(pid)
            if not proc_info:
                return

            # Create context menu
            menu = QMenu(self)

            # Priority submenu
            priority_menu = menu.addMenu("Set Priority")
            for priority in ProcessPriority:
                action = priority_menu.addAction(priority.name.capitalize())
                action.triggered.connect(lambda _, p=priority: self.set_process_priority_action(pid, p))

            # Add separator
            menu.addSeparator()

            # Memory actions
            limit_action = menu.addAction("Limit Memory")
            limit_action.triggered.connect(lambda: self.limit_process_action(pid))

            # Add separator
            menu.addSeparator()

            # Terminate action
            terminate_action = menu.addAction("Terminate Process")
            terminate_action.setForeground(QColor("#e74c3c"))
            terminate_action.triggered.connect(lambda: self.terminate_process_action(pid))

            # Show menu at cursor position
            menu.exec_(self.cursor().pos())

        except Exception as e:
            logging.error(f"Error showing process actions: {e}")

    def set_process_priority_action(self, pid: int, priority: ProcessPriority):
        """Set priority for specific process"""
        try:
            proc_info = self.system_monitor.process_history.get(pid)
            if proc_info:
                self.memory_optimizer.set_process_priority(proc_info.name, priority)
                self.notification_center.notify(
                    f"Set {proc_info.name} priority to {priority.name}",
                    NotificationType.INFO
                )
        except Exception as e:
            logging.error(f"Error setting process priority: {e}")

    def limit_process_action(self, pid: int):
        """Limit memory for specific process"""
        try:
            proc_info = self.system_monitor.process_history.get(pid)
            if not proc_info:
                return

            # Get memory limit from user
            limit, ok = QInputDialog.getInt(
                self, "Set Memory Limit",
                f"Set memory limit for {proc_info.name} (% of total RAM):",
                60, 10, 90, 5
            )

            if ok:
                self.memory_optimizer.set_process_priority(proc_info.name, ProcessPriority.LOW)

                # Apply the limit
                proc = psutil.Process(pid)
                total_ram = psutil.virtual_memory().total
                max_memory = int(total_ram * (limit / 100))

                if platform.system() == 'Windows':
                    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                    if handle:
                        try:
                            ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, 0, max_memory)
                            gc.collect()
                        finally:
                            ctypes.windll.kernel32.CloseHandle(handle)

                self.notification_center.notify(
                    f"Limited {proc_info.name} to {limit}% of total RAM",
                    NotificationType.SUCCESS
                )

        except Exception as e:
            logging.error(f"Error limiting process: {e}")

    def terminate_process_action(self, pid: int):
        """Terminate specific process"""
        try:
            proc_info = self.system_monitor.process_history.get(pid)
            if not proc_info:
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self, "Confirm Termination",
                f"Are you sure you want to terminate {proc_info.name} (PID: {pid})?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()

                    self.notification_center.notify(
                        f"Terminated {proc_info.name} (PID: {pid})",
                        NotificationType.WARNING
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    QMessageBox.warning(self, "Error", f"Could not terminate {proc_info.name}")

        except Exception as e:
            logging.error(f"Error terminating process: {e}")

    def toggle_game_mode(self, enabled: bool):
        """Toggle Game Mode on/off"""
        try:
            if enabled:
                # Get current settings
                ram_limit = self.game_ram_limit_spin.value()
                whitelist = [self.whitelist_list.item(i).text() for i in range(self.whitelist_list.count())]

                # Set performance profile
                profile_index = self.game_profile_combo.currentIndex()
                profiles = [PerformanceProfile.BALANCED, PerformanceProfile.GAMING,
                           PerformanceProfile.WORK, PerformanceProfile.BATTERY_SAVER]
                profile = profiles[profile_index]

                # Configure and start Game Mode
                self.game_mode.ram_limit_mb = ram_limit
                self.game_mode.whitelist = whitelist
                self.game_mode.set_performance_profile(profile)
                self.game_mode.aggressiveness = self.aggressiveness_slider.value()
                self.game_mode.start()

                self.game_mode_status.setText("Game Mode: ENABLED")
                self.game_mode_status.setStyleSheet("color: #2ecc71; font-weight: bold;")

            else:
                # Stop Game Mode
                self.game_mode.stop()
                self.game_mode_status.setText("Game Mode: DISABLED")
                self.game_mode_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

        except Exception as e:
            logging.error(f"Error toggling Game Mode: {e}")
            self.game_mode_toggle.setChecked(False)
            QMessageBox.critical(self, "Error", f"Failed to toggle Game Mode: {str(e)}")

    def update_game_profile(self, index: int):
        """Update Game Mode profile"""
        try:
            profiles = [PerformanceProfile.BALANCED, PerformanceProfile.GAMING,
                       PerformanceProfile.WORK, PerformanceProfile.BATTERY_SAVER]
            profile = profiles[index]

            # Update aggressiveness based on profile
            if profile == PerformanceProfile.GAMING:
                self.aggressiveness_slider.setValue(8)
                self.aggressiveness_label.setText("8")
            elif profile == PerformanceProfile.WORK:
                self.aggressiveness_slider.setValue(4)
                self.aggressiveness_label.setText("4")
            elif profile == PerformanceProfile.BATTERY_SAVER:
                self.aggressiveness_slider.setValue(6)
                self.aggressiveness_label.setText("6")
            else:  # Balanced
                self.aggressiveness_slider.setValue(5)
                self.aggressiveness_label.setText("5")

        except Exception as e:
            logging.error(f"Error updating game profile: {e}")

    def add_to_whitelist(self):
        """Add process to whitelist"""
        try:
            processes = self.whitelist_edit.text().strip()
            if not processes:
                return

            for proc in processes.split(','):
                proc = proc.strip().lower()
                if proc and proc not in [self.whitelist_list.item(i).text().lower() for i in range(self.whitelist_list.count())]:
                    self.whitelist_list.addItem(proc)

            self.whitelist_edit.clear()

        except Exception as e:
            logging.error(f"Error adding to whitelist: {e}")

    def remove_from_whitelist(self):
        """Remove selected process from whitelist"""
        try:
            for item in self.whitelist_list.selectedItems():
                self.whitelist_list.takeItem(self.whitelist_list.row(item))

        except Exception as e:
            logging.error(f"Error removing from whitelist: {e}")

    def optimize_now(self):
        """Perform immediate memory optimization"""
        try:
            # Update system info
            self.system_monitor.update_system_info()

            # Perform optimization
            self.memory_optimizer._apply_memory_optimization()

            self.notification_center.notify(
                "⚡ Memory optimization completed",
                NotificationType.SUCCESS
            )

        except Exception as e:
            logging.error(f"Error in optimize now: {e}")
            self.notification_center.notify(
                f"❌ Optimization failed: {str(e)}",
                NotificationType.ERROR
            )

    def toggle_auto_optimization(self, enabled: bool):
        """Toggle automatic optimization"""
        try:
            if enabled:
                self.memory_optimizer.start()
                self.toggle_auto_btn.setText("🤖 Auto Optimization: ON")
                self.notification_center.notify(
                    "Automatic optimization enabled",
                    NotificationType.SUCCESS
                )
            else:
                self.memory_optimizer.stop()
                self.toggle_auto_btn.setText("🤖 Auto Optimization: OFF")
                self.notification_center.notify(
                    "Automatic optimization disabled",
                    NotificationType.INFO
                )

        except Exception as e:
            logging.error(f"Error toggling auto optimization: {e}")
            self.toggle_auto_btn.setChecked(False)
            self.notification_center.notify(
                f"❌ Failed to toggle auto optimization: {str(e)}",
                NotificationType.ERROR
            )

    def start_auto_optimization(self):
        """Start automatic optimization based on settings"""
        try:
            if self.config_manager.current_config['advanced_settings']['auto_start']:
                self.memory_optimizer.set_memory_strategy(
                    MemoryManagementStrategy[self.config_manager.current_config['advanced_settings']['memory_strategy'].upper()]
                )
                self.memory_optimizer.start()
                self.toggle_auto_btn.setChecked(True)
                self.toggle_auto_btn.setText("🤖 Auto Optimization: ON")

        except Exception as e:
            logging.error(f"Error starting auto optimization: {e}")

    def load_settings(self):
        """Load settings from configuration"""
        try:
            config = self.config_manager.current_config

            # General settings
            self.auto_start_checkbox.setChecked(config['advanced_settings']['auto_start'])
            self.start_minimized_checkbox.setChecked(config['advanced_settings']['start_minimized'])

            # Memory settings
            strategy_index = ['balanced', 'aggressive', 'conservative'].index(
                config['advanced_settings']['memory_strategy'].lower()
            )
            self.memory_strategy_combo.setCurrentIndex(strategy_index)

            mode_index = ['automatic', 'manual', 'learning'].index(
                config['advanced_settings']['optimization_mode'].lower()
            )
            self.optimization_mode_combo.setCurrentIndex(mode_index)

            self.refresh_interval_spin.setValue(config['ui_settings']['refresh_interval'])

            # Notification settings
            self.enable_notifications_checkbox.setChecked(config['notification_settings']['enabled'])
            self.tray_notifications_checkbox.setChecked(config['notification_settings']['tray_notifications'])
            self.sound_notifications_checkbox.setChecked(config['notification_settings']['sound_enabled'])

            # Game Mode settings
            self.game_ram_limit_spin.setValue(config['game_mode_settings']['ram_limit'])
            self.whitelist_list.addItems(config['game_mode_settings']['whitelist'])

            profile_index = ['balanced', 'gaming', 'work', 'battery_saver'].index(
                config['game_mode_settings']['performance_profile'].lower()
            )
            self.game_profile_combo.setCurrentIndex(profile_index)

            # Apply memory strategy to optimizer
            self.memory_optimizer.set_memory_strategy(
                MemoryManagementStrategy[config['advanced_settings']['memory_strategy'].upper()]
            )

        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    def save_settings(self):
        """Save current settings to configuration"""
        try:
            config = self.config_manager.current_config

            # General settings
            config['advanced_settings']['auto_start'] = self.auto_start_checkbox.isChecked()
            config['advanced_settings']['start_minimized'] = self.start_minimized_checkbox.isChecked()

            # Memory settings
            strategies = ['balanced', 'aggressive', 'conservative']
            config['advanced_settings']['memory_strategy'] = strategies[self.memory_strategy_combo.currentIndex()]

            modes = ['automatic', 'manual', 'learning']
            config['advanced_settings']['optimization_mode'] = modes[self.optimization_mode_combo.currentIndex()]

            config['ui_settings']['refresh_interval'] = self.refresh_interval_spin.value()

            # Notification settings
            config['notification_settings']['enabled'] = self.enable_notifications_checkbox.isChecked()
            config['notification_settings']['tray_notifications'] = self.tray_notifications_checkbox.isChecked()
            config['notification_settings']['sound_enabled'] = self.sound_notifications_checkbox.isChecked()

            # Game Mode settings
            config['game_mode_settings']['ram_limit'] = self.game_ram_limit_spin.value()
            config['game_mode_settings']['whitelist'] = [
                self.whitelist_list.item(i).text() for i in range(self.whitelist_list.count())
            ]

            profiles = ['balanced', 'gaming', 'work', 'battery_saver']
            config['game_mode_settings']['performance_profile'] = profiles[self.game_profile_combo.currentIndex()]

            # Save configuration
            self.config_manager.save_config()

            self.notification_center.notify(
                "✅ Settings saved successfully",
                NotificationType.SUCCESS
            )

        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            self.notification_center.notify(
                f"❌ Failed to save settings: {str(e)}",
                NotificationType.ERROR
            )

    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('ram.ico'))

        tray_menu = QMenu()

        # Add menu items
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_normal)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)

        optimize_action = QAction("Optimize Now", self)
        optimize_action.triggered.connect(self.optimize_now)

        game_mode_action = QAction("Toggle Game Mode", self)
        game_mode_action.triggered.connect(lambda: self.game_mode_toggle.click())

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close)

        # Add actions to menu
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(optimize_action)
        tray_menu.addAction(game_mode_action)
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Connect tray icon click
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()

    def show_normal(self):
        """Show the window normally"""
        self.show()
        self.setWindowState(Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def export_analytics(self):
        """Export analytics data to file"""
        try:
            # Prepare data for export
            export_data = {
                'system_info': dict(self.system_monitor.system_info),
                'process_history': {
                    pid: {
                        'name': proc.name,
                        'memory_usage': proc.memory_usage,
                        'cpu_usage': proc.cpu_usage,
                        'priority': proc.priority.name
                    }
                    for pid, proc in self.system_monitor.process_history.items()
                },
                'health_history': list(self.health_scores) if hasattr(self, 'health_scores') else [],
                'memory_history': list(self.memory_usages) if hasattr(self, 'memory_usages') else [],
                'timestamp': datetime.now().isoformat(),
                'system_health': self.system_monitor.get_system_health().value
            }

            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Analytics Data", "",
                "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
            )

            if file_path:
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(export_data, f, indent=4)
                elif file_path.endswith('.csv'):
                    self._export_to_csv(export_data, file_path)
                else:
                    # Default to JSON
                    with open(file_path, 'w') as f:
                        json.dump(export_data, f, indent=4)

                self.notification_center.notify(
                    f"📊 Analytics exported to {file_path}",
                    NotificationType.SUCCESS
                )

        except Exception as e:
            logging.error(f"Error exporting analytics: {e}")
            self.notification_center.notify(
                f"❌ Export failed: {str(e)}",
                NotificationType.ERROR
            )

    def _export_to_csv(self, data: dict, file_path: str):
        """Export data to CSV format"""
        try:
            with open(file_path, 'w', newline='') as f:
                # Write system info
                f.write("System Information\n")
                for key, value in data['system_info'].items():
                    f.write(f"{key},{value}\n")

                f.write("\nProcess Information\n")
                f.write("Name,PID,Memory (MB),CPU (%),Priority\n")
                for pid, proc_data in data['process_history'].items():
                    f.write(f"{proc_data['name']},{pid},{proc_data['memory_usage']},{proc_data['cpu_usage']},{proc_data['priority']}\n")

                f.write("\nHealth History\n")
                f.write("Health Score\n")
                for score in data['health_history']:
                    f.write(f"{score}\n")

                f.write("\nMemory History\n")
                f.write("Memory Usage (MB)\n")
                for usage in data['memory_history']:
                    f.write(f"{usage}\n")

        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            raise

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Stop all running components
            self.memory_optimizer.stop()
            self.game_mode.stop()
            
            # Stop the monitoring worker thread
            if hasattr(self, 'monitoring_worker'):
                self.monitoring_worker.stop()

            # Save settings
            self.save_settings()

            # Confirm exit
            reply = QMessageBox.question(
                self, 'Exit', 'Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

        except Exception as e:
            logging.error(f"Error in close event: {e}")
            event.accept()

def main():
    """Main entry point for the enhanced RAM limiter"""
    try:
        # Setup logging
        logging.basicConfig(
            filename='ram_limiter_enhanced.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Create and run application
        app = QApplication(sys.argv)

        # Set application style
        app.setStyle('Fusion')

        # Create and show main window
        window = EnhancedRAMLimiterGUI()
        window.show()

        # Start application event loop
        sys.exit(app.exec_())

    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
