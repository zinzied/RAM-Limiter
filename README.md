# 🚀 RAM Limiter
<img width="1919" height="1015" alt="image" src="https://github.com/user-attachments/assets/71ec5d38-df76-4b2a-acde-cae1bbea6c36" />


**RAM Limiter** is a Windows utility with both GUI 🖥️ and CLI 💻, designed to monitor and limit the RAM usage of selected applications. It helps prevent memory-hungry apps (like Discord, Chrome, OBS, and more) from consuming excessive system resources, improving overall system performance—especially on PCs with limited RAM.

## ⭐ Key Features

- 📊 Limit RAM usage for multiple applications at once
- 🎯 Easy-to-use graphical interface and command-line options
- 🔧 Built-in support for popular apps (Discord, Chrome, OBS Studio, Visual Studio Code) and any custom process
- 📈 Real-time memory usage statistics and visualizations
- ⚙️ Configurable monitoring intervals and memory limits per process
- 🔄 System tray integration for background operation (GUI)
- 💾 Save/load configuration profiles (GUI)
- 📝 Automatic activity logging
- 🛡️ Requires admin privileges for optimal operation
- 🎮 Game Mode:
  - Automatically terminates non-essential processes that exceed RAM limits
  - Configurable RAM limit per process
  - Customizable process whitelist to protect critical applications
  - System processes are automatically protected
  - One-click activation/deactivation

## 🎮 Game Mode

Game Mode provides advanced memory optimization for gaming sessions by:

1. 🛡️ **Process Protection**: 
   - Whitelist critical processes you want to keep running
   - System processes are automatically protected
   - Comma-separated list for multiple processes

2. 📊 **RAM Management**:
   - Set maximum RAM limit per process (in MB)
   - Processes exceeding the limit are automatically terminated
   - Real-time monitoring and automatic intervention

3. ⚡ **Quick Controls**:
   - Enable/disable with a single click
   - Instant activation/deactivation
   - Status displayed in the output area

To use Game Mode:
1. Enter RAM limit (default: 500 MB)
2. Add processes to whitelist (comma-separated)
3. Click "Enable Game Mode" checkbox
4. Game Mode will automatically terminate non-whitelisted processes that exceed the RAM limit

> **Note:** Use Game Mode carefully as it terminates processes. Always whitelist important applications.

## 📖 Overview

RAM Limiter addresses the problem of applications caching excessive data and not releasing memory, which can slow down your system. By leveraging Windows memory management APIs and Python's garbage collection, RAM Limiter can free up unused memory, making more RAM available for games and other demanding applications.

![RAM Limiter Demonstration](https://user-images.githubusercontent.com/79897291/173233207-912f3cb1-bc42-45fa-9f81-36da025f58a4.gif)

> **Note:** The GUI version offers a modern, user-friendly experience with advanced features like memory usage graphs and configuration management.

## 🎮 Usage

### ⌨️ Command Line Options

```sh
python ram_limiter.py [options]

Options:
  --discord         🎮 Limit Discord RAM usage
  --chrome         🌐 Limit Chrome RAM usage
  --obs            🎥 Limit OBS RAM usage
  --vscode         💻 Limit Visual Studio Code RAM usage
  --custom         ✨ Limit RAM usage for custom processes
  --interval N     ⏱️ Monitoring interval in seconds (default: 5)
  --interactive    🖱️ Use interactive menu
  --test           🧪 Run a memory-hogging test
  --game-mode      🎮 Enable Game Mode
  --ram-limit N    📊 Set RAM limit per process in MB (default: 500)
  --whitelist      🛡️ Comma-separated list of processes to whitelist
```

### 🎮 Game Mode via CLI

You can activate Game Mode through command line with various options:

```sh
# Basic Game Mode with default settings
python ram_limiter.py --game-mode

# Game Mode with custom RAM limit (750 MB)
python ram_limiter.py --game-mode --ram-limit 750

# Game Mode with process whitelist
python ram_limiter.py --game-mode --whitelist "game.exe,steam.exe,discord.exe"

# Full example with all options
python ram_limiter.py --game-mode --ram-limit 1000 --whitelist "game.exe,steam.exe"
```

### 🖱️ Interactive Mode

Run the script without arguments to use the interactive menu:

```sh
python ram_limiter.py
```

The menu offers options to:
1. 🎮 Limit Discord
2. 🌐 Limit Chrome
3. 🎥 Limit OBS
4. 💻 Limit Visual Studio Code
5. 🔄 Limit Discord & Chrome together
6. ✨ Limit Custom Process(es)
7. 🎮 Enable Game Mode
0. 🚪 Exit

## 💻 System Requirements

- 🪟 Windows operating system
- 🐍 Python 3.x
- 📦 Required Python packages:
  - psutil
  - ctypes

## 📌 Notes

- ⚠️ The tool requires administrator privileges for optimal performance
- 🔒 Memory limits are capped at 2GB by default per process
- 📊 Default memory limit is set to 75% of total system RAM
- 📝 The tool logs all activities to `ram_limiter.log`

## 💡 Inspiration

Our version of the RAM Limiter improves upon [the original tool](https://github.com/farajyeet/discord-ram-limiter) by focusing on efficient memory management without overutilising the CPU. Some parts of the code were reused from the original repository and [0vm](https://github.com/0vm).

## 🏷️ Keywords

Memory Management | RAM Optimization | System Performance | Resource Monitoring | Windows Utility

### Donations
If you feel like showing your love and/or appreciation for this Sipmle project, then how about shouting me a coffee or Milk :)

[<img src="https://github.com/zinzied/Website-login-checker/assets/10098794/24f9935f-3637-4607-8980-06124c2d0225">](https://www.buymeacoffee.com/Zied)
