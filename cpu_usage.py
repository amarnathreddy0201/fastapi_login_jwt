import psutil
import logging
import platform
import subprocess

# Logger configuration
logger = logging.getLogger(__name__)

def get_cpu_usage():
    os_type = platform.system()
    logger.info(f"Detected OS: {os_type}")

    if os_type == "Windows":
        return get_cpu_usage_windows()
    elif os_type == "Linux":
        return get_cpu_usage_linux()
    elif os_type == "Darwin":  # macOS
        return get_cpu_usage_mac()
    else:
        logger.error(f"Unsupported OS: {os_type}")
        return "Unsupported OS"

def get_cpu_usage_windows():
    logger.info("Getting CPU usage for Windows")
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_usage_str = f"{cpu_usage}%"
        logger.info(f"CPU usage: {cpu_usage_str}")
        return cpu_usage_str
    except Exception as e:
        logger.error(f"Error obtaining CPU usage on Windows: {e}")
        return "Error obtaining CPU usage"

def get_cpu_usage_linux():
    logger.info("Getting CPU usage for Linux")
    try:
        command = "ps -eo pcpu | awk 'NR>1 {sum += $1} END {print sum}'"
        result = subprocess.run(command, capture_output=True, shell=True, text=True)
        if result.returncode == 0:
            cpu_usage = result.stdout.strip() + '%'
            logger.info(f"CPU usage: {cpu_usage}")
            return cpu_usage
        else:
            logger.error("Error obtaining CPU usage on Linux")
            return "Error obtaining CPU usage"
    except Exception as e:
        logger.error(f"Error obtaining CPU usage on Linux: {e}")
        return "Error obtaining CPU usage"

def get_cpu_usage_mac():
    logger.info("Getting CPU usage for macOS")
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_usage_str = f"{cpu_usage}%"
        logger.info(f"CPU usage: {cpu_usage_str}")
        return cpu_usage_str
    except Exception as e:
        logger.error(f"Error obtaining CPU usage on macOS: {e}")
        return "Error obtaining CPU usage"

# Example usage
if __name__ == "__main__":
    print(get_cpu_usage())
