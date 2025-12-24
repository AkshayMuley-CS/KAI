import psutil
import platform

def get_system(config, args=None):
    return f"System: {platform.system()}\nCPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%"

def register(config):
    return {'system': get_system}