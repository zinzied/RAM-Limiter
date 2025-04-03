import os
import sys
import time
import psutil
import ctypes
import argparse
import threading
import ctypes
from ctypes import wintypes

# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF

# Windows API functions
kernel32 = ctypes.windll.kernel32
GlobalMemoryStatusEx = kernel32.GlobalMemoryStatusEx
SetProcessWorkingSetSize = kernel32.SetProcessWorkingSetSize
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    if not is_admin():
        print("RAM Limiter requires admin privileges.")
        print("Would you like to restart the script with admin privileges? (y/n)")
        choice = input().lower()
        if choice == 'y':
            args = [sys.executable] + sys.argv + ['--interactive']
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(args), None, 1)
            sys.exit(0)
        else:
            print("The script will continue without admin privileges, but functionality may be limited.")
            print("Press Enter to continue...")
            input()

def get_process_id_by_name(name):
    pids = []
    chrome_names = ["chrome", "chrome.exe", "Google Chrome"]
    target_names = [name.lower()] if name.lower() != "chrome" else [n.lower() for n in chrome_names]
    
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if any(target_name in proc.info['name'].lower() for target_name in target_names):
                pids.append((proc.pid, proc.info['memory_info'].rss))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if pids:
        return max(pids, key=lambda x: x[1])[0]
    return None

def limit_ram_for_process(name, interval, max_memory_percent=75):
    print(f"Limiting RAM usage for {name}...")
    while True:
        pid = get_process_id_by_name(name)
        if pid is None:
            print(f"{name} process not found. Retrying...")
            time.sleep(interval)
            continue

        try:
            process = psutil.Process(pid)

            # Get system memory info
            total_ram = psutil.virtual_memory().total
            max_memory = int(total_ram * (max_memory_percent / 100))

            # Cap max_memory to 2GB (adjust if needed)
            max_memory = min(max_memory, 2 * 1024 * 1024 * 1024)

            # Open process with all access
            handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if handle:
                # Set working set size
                try:
                    current_min, current_max = process.memory_info().wset, process.memory_info().peak_wset
                    new_min = max(current_min, int(max_memory * 0.5))  # Set minimum to half of max or current, whichever is larger
                    SetProcessWorkingSetSize(handle, new_min, max_memory)
                finally:
                    CloseHandle(handle)

            # Get current memory usage
            mem = process.memory_info()
            ram_usage = (mem.rss / total_ram) * 100
            print(f"{name.upper()}: RAM usage: {ram_usage:.2f}% | {mem.rss / (1024 * 1024):.2f} MB (Limited to {max_memory_percent}%)")
        except Exception as ex:
            print(f"Error limiting RAM for {name}: {str(ex)}")

        time.sleep(interval)


def custom_ram_limiter(process_names, interval, max_memory_percent):
    for name in process_names:
        threading.Thread(target=limit_ram_for_process, args=(name, interval, max_memory_percent), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping RAM limiting...")

def interactive_menu():
    while True:
        print("\nRAM Limiter Menu:")
        print("1. Limit Discord")
        print("2. Limit Chrome")
        print("3. Limit OBS")
        print("4. Limit Discord & Chrome")
        print("5. Limit Custom Process")
        print("0. Exit")

        choice = input("Enter your choice (0-5): ")

        if choice == '0':
            print("Exiting RAM Limiter...")
            sys.exit(0)
        elif choice in ['1', '2', '3', '4', '5']:
            interval = int(input("Enter monitoring interval in seconds (default 5): ") or "5")
            max_memory_percent = int(input("Enter maximum memory percentage (default 75): ") or "75")
            processes = []
            if choice == '1':
                processes = ["discord"]
            elif choice == '2':
                processes = ["chrome"]
            elif choice == '3':
                processes = ["obs64"]
            elif choice == '4':
                processes = ["discord", "chrome"]
            elif choice == '5':
                custom = input("Enter custom process names (comma-separated): ")
                processes = [p.strip() for p in custom.split(',')]

            return processes, interval, max_memory_percent
        else:
            print("Invalid choice. Please try again.")


def main():
    elevate_privileges()

    parser = argparse.ArgumentParser(description="RAM Limiter CLI")
    parser.add_argument("--discord", action="store_true", help="Limit Discord RAM usage")
    parser.add_argument("--chrome", action="store_true", help="Limit Chrome RAM usage")
    parser.add_argument("--obs", action="store_true", help="Limit OBS RAM usage")
    parser.add_argument("--custom", nargs="+", metavar="PROCESS", help="Limit RAM usage for custom processes")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in seconds (default: 5)")
    parser.add_argument("--interactive", action="store_true", help="Use interactive menu")
    args = parser.parse_args()

    if args.interactive or len(sys.argv) == 1:
        processes_to_monitor, interval, max_memory_percent = interactive_menu()
    else:
        processes_to_monitor = []
        if args.discord:
            processes_to_monitor.append("discord")
        if args.chrome:
            processes_to_monitor.append("chrome")
        if args.obs:
            processes_to_monitor.append("obs64")
        if args.custom:
            processes_to_monitor.extend(args.custom)
        interval = args.interval
        max_memory_percent = 75  # default value for non-interactive mode

    if not processes_to_monitor:
        print("No processes selected to monitor.")
        sys.exit(1)

    custom_ram_limiter(processes_to_monitor, interval, max_memory_percent)

if __name__ == "__main__":
    main()

