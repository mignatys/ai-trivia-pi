# -----------------------------------------------------------------------------
# Raspberry Pi Load and Temperature Monitor (load.py)
#
# REQUIREMENTS:
# 1. Raspberry Pi OS (for vcgencmd utility)
# 2. Python library psutil:
#    $ pip install psutil
# -----------------------------------------------------------------------------

import os
import time
import subprocess
import psutil

# --- Configuration and ANSI Color Codes ---

# ANSI Color Definitions (Used for coloring the terminal output)
GREEN = '\033[92m'
ORANGE = '\033[93m'  # Yellow is used for "orange" in most terminals
RED = '\033[91m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Temperature Thresholds (in Celsius)
# These are typical safe, warning, and critical thresholds for a Raspberry Pi SoC.
TEMP_SAFE_MAX = 60.0    # Green: Below this is safe
TEMP_WARNING = 70.0   # Orange: Above this is a warning
TEMP_HOT = 72.0       # Red: Above this is critically hot
TEMP_COOLDOWN_TRIGGER = TEMP_HOT + 2.0 # 74.0: Triggers the "COOL DOWN" message

# --- Utility Functions ---

def get_cpu_temp():
    """
    Retrieves the CPU temperature using the Raspberry Pi specific 'vcgencmd' utility.
    Returns the temperature as a float, or None if the command fails.
    """
    try:
        # Run the vcgencmd command
        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse the output: temp=52.3'C
        temp_str = result.stdout.strip()
        temp_value = float(temp_str.split('=')[1].split("'")[0])
        return temp_value
    except (subprocess.CalledProcessError, IndexError, ValueError) as e:
        # Fallback if vcgencmd is missing or output is unexpected
        print(f"{RED}Error reading temperature via vcgencmd. Is this a Pi?{RESET}")
        print(f"Details: {e}")
        # Try reading the standard Linux thermal file as a fallback
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_raw = f.read().strip()
                return float(temp_raw) / 1000.0
        except Exception:
            return None

def get_temp_color(temp):
    """Returns the ANSI color code based on the temperature value."""
    if temp is None:
        return WHITE
    if temp >= TEMP_COOLDOWN_TRIGGER:
        return RED
    elif temp >= TEMP_HOT:
        return RED
    elif temp >= TEMP_WARNING:
        return ORANGE
    else:
        return GREEN

def display_stats():
    """Fetches, processes, and displays the system statistics."""
    # 1. Clear the terminal screen
    os.system('clear')

    # 2. Get Data
    temp = get_cpu_temp()
    
    # psutil.cpu_percent returns a list of per-core usage if percpu=True
    # interval=0 means non-blocking, but relies on previous call for comparison.
    # We call it once per refresh.
    cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
    cpu_total = sum(cpu_cores) / len(cpu_cores)
    
    # 3. Apply Colors and Status Messages

    temp_color = get_temp_color(temp)
    temp_display = f"{temp:.1f}C" if temp is not None else "N/A"
    
    # 4. Print Header
    print(f"{BOLD}{WHITE}--- Raspberry Pi System Monitor ---{RESET}")
    print("Refresh Rate: 1.0s")
    print("-" * 35)

    # 5. Print Temperature
    print(f"{BOLD}CPU Temperature:{RESET} {temp_color}{temp_display}{RESET}")
    
    # Check for cool down message
    if temp is not None and temp >= TEMP_COOLDOWN_TRIGGER:
        print(f"{RED}{BOLD}!!! CRITICAL: INITIATE COOL DOWN! !!!{RESET}")
    elif temp is not None and temp >= TEMP_HOT:
        print(f"{RED}Warning: High Temperature. Check Cooling.{RESET}")
    
    # 6. Print Total CPU Load
    print("-" * 35)
    print(f"{BOLD}Total CPU Load:{RESET} {ORANGE}{cpu_total:.2f}%{RESET}")
    print("-" * 35)

    # 7. Print Per-Core Load
    print(f"{BOLD}Core Loads ({len(cpu_cores)} cores):{RESET}")
    
    for i, core_load in enumerate(cpu_cores):
        # Color core load based on usage (optional, using default green for now)
        core_color = GREEN if core_load < 60 else ORANGE if core_load < 90 else RED
        print(f"  - Core {i}: {core_color}{core_load:.2f}%{RESET}")

    print("-" * 35)


# --- Main Execution Loop ---

if __name__ == "__main__":
    # Check if psutil is installed (just a quick check, usually safer to rely on pip)
    if 'psutil' not in globals():
        print(f"{RED}The 'psutil' library is required. Please run: pip install psutil{RESET}")
        exit(1)

    # Main monitoring loop
    try:
        while True:
            display_stats()
            # Wait for 1 second before the next update
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C
        os.system('clear')
        print(f"{BOLD}Monitoring stopped. Goodbye!{RESET}")
    except Exception as e:
        # Handle other unexpected errors
        os.system('clear')
        print(f"{RED}An unexpected error occurred: {e}{RESET}")
