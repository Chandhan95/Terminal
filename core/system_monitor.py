import psutil
import platform
import time
from typing import Dict, List, Any
from datetime import datetime

class SystemMonitor:
    """
    System monitoring utilities for the terminal
    """
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information and usage"""
        return {
            'physical_cores': psutil.cpu_count(logical=False),
            'total_cores': psutil.cpu_count(logical=True),
            'max_frequency': f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "N/A",
            'current_frequency': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A",
            'cpu_usage_per_core': psutil.cpu_percent(percpu=True, interval=1),
            'total_cpu_usage': psutil.cpu_percent(interval=1)
        }
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information and usage"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_memory': SystemMonitor._bytes_to_human(memory.total),
            'available_memory': SystemMonitor._bytes_to_human(memory.available),
            'used_memory': SystemMonitor._bytes_to_human(memory.used),
            'memory_percentage': memory.percent,
            'total_swap': SystemMonitor._bytes_to_human(swap.total),
            'used_swap': SystemMonitor._bytes_to_human(swap.used),
            'swap_percentage': swap.percent
        }
    
    @staticmethod
    def get_disk_info() -> List[Dict[str, Any]]:
        """Get disk information and usage"""
        disks = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'file_system': partition.fstype,
                    'total_size': SystemMonitor._bytes_to_human(partition_usage.total),
                    'used': SystemMonitor._bytes_to_human(partition_usage.used),
                    'free': SystemMonitor._bytes_to_human(partition_usage.free),
                    'percentage': (partition_usage.used / partition_usage.total) * 100
                })
            except PermissionError:
                # This can happen on Windows
                continue
        
        return disks
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network information"""
        network_io = psutil.net_io_counters()
        
        return {
            'bytes_sent': SystemMonitor._bytes_to_human(network_io.bytes_sent),
            'bytes_received': SystemMonitor._bytes_to_human(network_io.bytes_recv),
            'packets_sent': network_io.packets_sent,
            'packets_received': network_io.packets_recv
        }
    
    @staticmethod
    def get_process_list(limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of running processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                proc_info = proc.info
                proc_info['cpu_percent'] = proc.cpu_percent()
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:limit]
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get general system information"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            'uptime': str(datetime.now() - boot_time).split('.')[0]  # Remove microseconds
        }
    
    @staticmethod
    def _bytes_to_human(bytes_value: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    @staticmethod
    def get_top_processes(limit: int = 10) -> str:
        """Get top processes in a formatted string similar to 'top' command"""
        processes = SystemMonitor.get_process_list(limit)
        
        # Header
        result = [
            f"{'PID':>7} {'PPID':>7} {'CPU%':>6} {'MEM%':>6} {'STATUS':>10} {'NAME'}",
            "-" * 60
        ]
        
        # Process list
        for proc in processes:
            result.append(
                f"{proc['pid']:>7} {proc['ppid'] or 0:>7} "
                f"{proc['cpu_percent']:>5.1f} {proc['memory_percent']:>5.1f} "
                f"{proc['status']:>10} {proc['name']}"
            )
        
        return '\n'.join(result)
    
    @staticmethod
    def get_system_summary() -> str:
        """Get a comprehensive system summary"""
        cpu_info = SystemMonitor.get_cpu_info()
        memory_info = SystemMonitor.get_memory_info()
        system_info = SystemMonitor.get_system_info()
        
        summary = f"""System Information:
Platform: {system_info['platform']} {system_info['platform_release']}
Architecture: {system_info['architecture']}
Processor: {system_info['processor']}
Boot Time: {system_info['boot_time']}
Uptime: {system_info['uptime']}

CPU Information:
Physical Cores: {cpu_info['physical_cores']}
Total Cores: {cpu_info['total_cores']}
Max Frequency: {cpu_info['max_frequency']}
Current Frequency: {cpu_info['current_frequency']}
CPU Usage: {cpu_info['total_cpu_usage']}%

Memory Information:
Total Memory: {memory_info['total_memory']}
Available Memory: {memory_info['available_memory']}
Used Memory: {memory_info['used_memory']} ({memory_info['memory_percentage']}%)
Total Swap: {memory_info['total_swap']}
Used Swap: {memory_info['used_swap']} ({memory_info['swap_percentage']}%)"""

        return summary

# Terminal commands that use SystemMonitor
def command_top(args: List[str]) -> str:
    """Top command implementation"""
    limit = 10
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            pass
    
    return SystemMonitor.get_top_processes(limit)

def command_free(args: List[str]) -> str:
    """Free command implementation"""
    memory_info = SystemMonitor.get_memory_info()
    
    return f"""              total        used        free      shared  buff/cache   available
Mem:     {memory_info['total_memory']:>10} {memory_info['used_memory']:>10} N/A        N/A        N/A {memory_info['available_memory']:>10}
Swap:    {memory_info['total_swap']:>10} {memory_info['used_swap']:>10} N/A"""

def command_df(args: List[str]) -> str:
    """Disk free command implementation"""
    disks = SystemMonitor.get_disk_info()
    
    result = ["Filesystem      Size  Used Avail Use% Mounted on"]
    for disk in disks:
        result.append(
            f"{disk['device']:<15} {disk['total_size']:>5} {disk['used']:>5} "
            f"{disk['free']:>5} {disk['percentage']:>3.0f}% {disk['mountpoint']}"
        )
    
    return '\n'.join(result)

def command_uptime(args: List[str]) -> str:
    """Uptime command implementation"""
    system_info = SystemMonitor.get_system_info()
    cpu_info = SystemMonitor.get_cpu_info()
    
    return f"up {system_info['uptime']}, load average: {cpu_info['total_cpu_usage']:.2f}%"

def command_systeminfo(args: List[str]) -> str:
    """System info command implementation"""
    return SystemMonitor.get_system_summary()