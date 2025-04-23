import os
import sys
import time
import psutil
import ctypes
import argparse
import threading
import logging
import gc
from ctypes import wintypes
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)
# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF

# Add a dictionary to store colors for different processes
PROCESS_COLORS = {
    "chrome": Fore.YELLOW,
    "discord": Fore.MAGENTA,
    "obs64": Fore.CYAN,
    "Code": Fore.BLUE,
}
# Windows API functions
kernel32 = ctypes.windll.kernel32
GlobalMemoryStatusEx = kernel32.GlobalMemoryStatusEx
SetProcessWorkingSetSize = kernel32.SetProcessWorkingSetSize
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle

# Add this new class after the existing imports
class GameMode:
    def __init__(self, ram_limit_mb=500, whitelist=None):
        self.ram_limit_mb = ram_limit_mb
        self.whitelist = whitelist or ['explorer.exe', 'system', 'systemd', 
                                     'svchost.exe', 'csrss.exe', 'winlogon.exe', 
                                     'services.exe']
        self.running = True

    def start(self):
        print(f"{Fore.GREEN}Game Mode activated. RAM limit: {self.ram_limit_mb}MB{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Whitelisted processes: {', '.join(self.whitelist)}{Style.RESET_ALL}")
        while self.running:
            try:
                for proc in psutil.process_iter(['name', 'memory_info']):
                    try:
                        if proc.name().lower() not in self.whitelist:
                            memory_mb = proc.memory_info().rss / (1024 * 1024)
                            if memory_mb > self.ram_limit_mb:
                                proc.kill()
                                print(f"{Fore.RED}Terminated {proc.name()} using {memory_mb:.2f}MB{Style.RESET_ALL}")
                                logging.info(f"Game Mode terminated {proc.name()} using {memory_mb:.2f}MB")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(2)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
        print(f"{Fore.YELLOW}Game Mode deactivated{Style.RESET_ALL}")

def setup_logging():
    logging.basicConfig(filename='ram_limiter.log', level=logging.INFO,
                        format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    logging.info(f"Started monitoring {name}")
    process_color = PROCESS_COLORS.get(name.lower(), Fore.WHITE)
    while True:
        pid = get_process_id_by_name(name)
        if pid is None:
            print(f"{name} process not found. Retrying...")
            logging.warning(f"{name} process not found")
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
                try:
                    # Empty working set
                    SetProcessWorkingSetSize(handle, -1, -1)
                    time.sleep(0.1)

                    # Set new working set size
                    SetProcessWorkingSetSize(handle, 0, max_memory)

                    # Trim working set
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                finally:
                    CloseHandle(handle)

            # Force garbage collection
            gc.collect()
            # Get current memory usage
            mem = process.memory_info()
            ram_usage = (mem.rss / total_ram) * 100
            working_set = (mem.wset / total_ram) * 100
            private_usage = (mem.private / total_ram) * 100

            log_message = (f"{process_color}{name.upper()}: "
                           f"RAM usage (RSS): {ram_usage:.2f}% | {mem.rss / (1024 * 1024):.2f} MB, "
                           f"Working Set: {working_set:.2f}% | {mem.wset / (1024 * 1024):.2f} MB, "
                           f"Private Usage: {private_usage:.2f}% | {mem.private / (1024 * 1024):.2f} MB "
                           f"(Limited to {max_memory_percent}%){Style.RESET_ALL}")
            print(log_message)
            logging.info(log_message)

            # If the process is using more than the limit, try to reduce it more aggressively
            if ram_usage > max_memory_percent:
                print(f"{Fore.RED}Attempting to reduce {name} memory usage more aggressively...{Style.RESET_ALL}")
                if handle:
                    try:
                        SetProcessWorkingSetSize(handle, 0, max_memory // 2)  # Set to half of max_memory
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                    finally:
                        CloseHandle(handle)

                # Try to free up memory by calling the garbage collector multiple times
                for _ in range(3):
                    gc.collect()
        except Exception as ex:
            error_message = f"{Fore.RED}Error limiting RAM for {name}: {str(ex)}{Style.RESET_ALL}"
            print(error_message)
            logging.error(error_message)

        time.sleep(interval)

def print_system_memory():
    mem = psutil.virtual_memory()
    print(f"\n{Fore.GREEN}System Memory: {mem.percent}% used | {mem.used / (1024 * 1024):.2f} MB used | {mem.available / (1024 * 1024):.2f} MB available{Style.RESET_ALL}")

def custom_ram_limiter(process_names, interval, max_memory_percent):
    for name in process_names:
        threading.Thread(target=limit_ram_for_process, args=(name, interval, max_memory_percent), daemon=True).start()

    try:
        while True:
            time.sleep(10)  # Print system memory every 10 seconds
            print_system_memory()
    except KeyboardInterrupt:
        print("\nStopping RAM limiting...")

def interactive_menu():
    while True:
        print(f"\n{Fore.CYAN}RAM Limiter Menu:{Style.RESET_ALL}")
        print("1. Limit Discord")
        print("2. Limit Chrome")
        print("3. Limit OBS")
        print("4. Limit Visual Studio Code")
        print("5. Limit Discord & Chrome")
        print("6. Limit Custom Process")
        print("7. Enable Game Mode")
        print("0. Exit")

        choice = input(f"{Fore.GREEN}Enter your choice (0-7): {Style.RESET_ALL}")

        if choice == '0':
            print("Exiting RAM Limiter...")
            sys.exit(0)
        elif choice == '7':
            ram_limit = int(input("Enter RAM limit per process in MB (default 500): ") or "500")
            whitelist = input("Enter whitelisted processes (comma-separated, leave empty for defaults): ")
            whitelist = [p.strip().lower() for p in whitelist.split(',')] if whitelist else None
            game_mode = GameMode(ram_limit_mb=ram_limit, whitelist=whitelist)
            game_mode.start()
            return [], 0, 0  # Return empty values as game mode handles everything
        elif choice in ['1', '2', '3', '4', '5', '6']:
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
                processes = ["Code"]  # VS Code process name
            elif choice == '5':
                processes = ["discord", "chrome"]
            elif choice == '6':
                custom = input("Enter custom process names (comma-separated): ")
                processes = [p.strip() for p in custom.split(',')]

            return processes, interval, max_memory_percent
        else:
            print("Invalid choice. Please try again.")

def print_animated_welcome():
    welcome_message = """
                ██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗███████╗
                ██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║██╔════╝
                ██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║█████╗  
                ██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║██╔══╝  
                ╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗
                ╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
                                                                            
                ████████╗ ██████╗     ██████╗  █████╗ ███╗   ███╗             
                ╚══██╔══╝██╔═══██╗    ██╔══██╗██╔══██╗████╗ ████║             
                   ██║   ██║   ██║    ██████╔╝███████║██╔████╔██║             
                   ██║   ██║   ██║    ██╔══██╗██╔══██║██║╚██╔╝██║             
                   ██║   ╚██████╔╝    ██║  ██║██║  ██║██║ ╚═╝ ██║             
                   ╚═╝    ╚═════╝     ╚═╝  ╚═╝╚═╝  ██║██║ ╚═╝ ██║             
                                                                            
                ██╗     ██╗███╗   ███╗██╗████████╗███████╗██████╗             
                ██║     ██║████╗ ████║██║╚══██╔══╝██╔════╝██╔══██╗            
                ██║     ██║██╔████╔██║██║   ██║   █████╗  ██████╔╝            
                ██║     ██║██║╚██╔╝██║██║   ██║   ██╔══╝  ██╔══██╗            
                ███████╗██║██║ ╚═╝ ██║██║   ██║   ███████╗██║  ██║            
                ╚══════╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝            
    """
    description = "Optimize your system's memory usage for better performance!"
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]

    # Print the ASCII art welcome message
    for i, char in enumerate(welcome_message):
        color = colors[i % len(colors)]
        sys.stdout.write(f"{color}{char}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(0.001)  # Faster animation for the large text

    # Print the description
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{description}{Style.RESET_ALL}")

    # Add some space after the welcome message
    print("\n" + "=" * 70 + "\n")

def main():
    print_animated_welcome()
    setup_logging()

    parser = argparse.ArgumentParser(description="RAM Limiter CLI")
    parser.add_argument("--discord", action="store_true", help="Limit Discord RAM usage")
    parser.add_argument("--chrome", action="store_true", help="Limit Chrome RAM usage")
    parser.add_argument("--obs", action="store_true", help="Limit OBS RAM usage")
    parser.add_argument("--vscode", action="store_true", help="Limit Visual Studio Code RAM usage")
    parser.add_argument("--custom", nargs="+", metavar="PROCESS", help="Limit RAM usage for custom processes")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in seconds (default: 5)")
    parser.add_argument("--interactive", action="store_true", help="Use interactive menu")
    parser.add_argument("--test", action="store_true", help="Run a memory-hogging test")
    parser.add_argument("--game-mode", action="store_true", help="Enable Game Mode")
    parser.add_argument("--ram-limit", type=int, default=500, help="RAM limit per process in MB for Game Mode")
    parser.add_argument("--whitelist", type=str, help="Comma-separated list of processes to whitelist in Game Mode")
    args = parser.parse_args()

    if args.game_mode:
        whitelist = [p.strip().lower() for p in args.whitelist.split(',')] if args.whitelist else None
        game_mode = GameMode(ram_limit_mb=args.ram_limit, whitelist=whitelist)
        game_mode.start()
        return

    if args.test:
        print("Running memory hog test...")
        threading.Thread(target=memory_hog, daemon=True).start()
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
        if args.vscode:
            processes_to_monitor.append("Code")
        if args.custom:
            processes_to_monitor.extend(args.custom)
        interval = args.interval
        max_memory_percent = 75  # default value for non-interactive mode

    if not processes_to_monitor:
        print("No processes selected to monitor.")
        sys.exit(1)

    custom_ram_limiter(processes_to_monitor, interval, max_memory_percent)


def memory_hog():
    # Allocate a large list to consume memory
    large_list = [0] * (1024 * 1024 * 100)  # Allocate about 800 MB
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()

