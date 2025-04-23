# RAM Limiter

**RAM Limiter** is a Windows utility with both GUI and CLI, designed to monitor and limit the RAM usage of selected applications. It helps prevent memory-hungry apps (like Discord, Chrome, OBS, and more) from consuming excessive system resources, improving overall system performance—especially on PCs with limited RAM.

## Key Features

- Limit RAM usage for multiple applications at once
- Easy-to-use graphical interface and command-line options
- Built-in support for popular apps (Discord, Chrome, OBS Studio, Visual Studio Code) and any custom process
- Real-time memory usage statistics and visualizations
- Configurable monitoring intervals and memory limits per process
- System tray integration for background operation (GUI)
- Save/load configuration profiles (GUI)
- Automatic activity logging
- Requires admin privileges for optimal operation

## Overview

RAM Limiter addresses the problem of applications caching excessive data and not releasing memory, which can slow down your system. By leveraging Windows memory management APIs and Python's garbage collection, RAM Limiter can free up unused memory, making more RAM available for games and other demanding applications.

![RAM Limiter Demonstration](https://user-images.githubusercontent.com/79897291/173233207-912f3cb1-bc42-45fa-9f81-36da025f58a4.gif)

> **Note:** The GUI version offers a modern, user-friendly experience with advanced features like memory usage graphs and configuration management.

## Usage

### Interactive Mode

Run the script without arguments to use the interactive menu:

```sh
python ram_limiter.py
```

The menu offers options to:
1. Limit Discord
2. Limit Chrome
3. Limit OBS
4. Limit Visual Studio Code
5. Limit Discord & Chrome together
6. Limit Custom Process(es)
0. Exit

### Command Line Options

```sh
python ram_limiter.py [options]

Options:
  --discord         Limit Discord RAM usage
  --chrome         Limit Chrome RAM usage
  --obs            Limit OBS RAM usage
  --vscode         Limit Visual Studio Code RAM usage
  --custom [PROCESSES...]
                   Limit RAM usage for custom processes
  --interval N     Monitoring interval in seconds (default: 5)
  --interactive    Use interactive menu
  --test           Run a memory-hogging test
```

### Examples

Limit Discord and Chrome with 5-second monitoring interval:
```sh
python ram_limiter.py --discord --chrome --interval 5
```

Monitor custom applications:
```sh
python ram_limiter.py --custom firefox spotify --interval 10
```

## System Requirements

- Windows operating system
- Python 3.x
- Required Python packages:
  - psutil
  - ctypes

## Notes

- The tool requires administrator privileges for optimal performance
- Memory limits are capped at 2GB by default per process
- Default memory limit is set to 75% of total system RAM
- The tool logs all activities to `ram_limiter.log`

## Inspiration
[This Tool](https://github.com/farajyeet/discord-ram-limiter) is no longer maintained. It was found to consume more CPU resources than Discord itself, resulting in a trade-off between free CPU and free RAM. This not only led to increased power usage but also negated the purpose of freeing up RAM.

Our version of the RAM Limiter improves upon the original by focusing on efficient memory management without overutilising the CPU. Some parts of the code were reused from the original repository and [0vm](https://github.com/0vm).

## Tags

- Limit RAM usage in Discord, 
- Limit RAM usage in Google Chrome, 
- Reduce RAM consumption in Google Chrome, 
- High RAM usage in Google Chrome, 
- Discord RAM management, 
- Reduce Discord's memory usage, 
- Discord RAM optimization, 
- Discord RAM optimisation, 
- Memory leak in Discord, 
- High RAM usage in Discord, 
- OBS RAM management, 
- Reduce OBS memory usage, 
- OBS RAM optimization, 
- OBS RAM optimisation, 
- OBS memory leak troubleshooting, 
- High RAM usage in OBS, 
- Limit OBS RAM usage,
- VS Code RAM management,
- Multi-process RAM limiter,
- Windows memory optimization tool
