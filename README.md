# RAM Limiter

A Python utility designed to optimize RAM usage of applications through Windows memory management APIs.

## Features

- Monitor and limit RAM usage for multiple applications simultaneously
- Interactive menu interface and command-line options
- Support for popular applications:
  - Discord
  - Google Chrome
  - OBS Studio
  - Visual Studio Code
  - Custom processes
- Real-time memory usage statistics
- Configurable monitoring intervals
- Adjustable memory limits per process
- Automatic logging of memory usage
- Admin privilege elevation when needed

## Overview
Old Video, Now you can limit any application and as many applications.

![RAM Limiter Demonstration](https://user-images.githubusercontent.com/79897291/173233207-912f3cb1-bc42-45fa-9f81-36da025f58a4.gif)
https://user-images.githubusercontent.com/79897291/172990167-0e113c2d-5edd-4ffa-9e06-8ac7cb1946ea.mp4
(The wallpaper was a meme back then, I do not condone the actions of foreign governments)

RAM Limiter was developed to address the challenge of applications, like Discord, that tend to cache objects unnecessarily, leading to high RAM usage. It leverages the `GC.Collect` method for efficient garbage collection, thereby freeing up the memory that these applications consume.

This tool proves particularly useful for systems with limited RAM, where applications like Discord could use up to 1.3GB. By releasing these resources, it allows RAM-intensive games and other applications to run more smoothly.

The RAM Limiter is a standalone solution that eliminates the need for other software like Razer Cortex™. Moreover, it provides an updated and maintained alternative to the original version of this tool, which is no longer supported and has been outdated for over a year.

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
