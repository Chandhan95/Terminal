import os
import sys
import subprocess
import shlex
import psutil
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import platform
import time
import glob
import shutil

class PythonTerminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.command_history = []
        self.environment_vars = dict(os.environ)
        self.built_in_commands = {
            'cd': self._cd,
            'pwd': self._pwd,
            'ls': self._ls,
            'dir': self._ls,  # Windows compatibility
            'mkdir': self._mkdir,
            'rmdir': self._rmdir,
            'rm': self._rm,
            'del': self._rm,  # Windows compatibility
            'cp': self._cp,
            'copy': self._cp,  # Windows compatibility
            'mv': self._mv,
            'move': self._mv,  # Windows compatibility
            'cat': self._cat,
            'type': self._cat,  # Windows compatibility
            'echo': self._echo,
            'clear': self._clear,
            'cls': self._clear,  # Windows compatibility
            'exit': self._exit,
            'history': self._history,
            'ps': self._ps,
            'top': self._top,
            'df': self._df,
            'free': self._free,
            'whoami': self._whoami,
            'env': self._env,
            'export': self._export,
            'find': self._find,
            'grep': self._grep,
            'touch': self._touch,
            'help': self._help,
            # Add command aliases for natural language
            'list': self._ls,
            'show': self._cat,
            'display': self._cat,
            'create': self._touch,
            'delete': self._rm,
            'remove': self._rm,
        }
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command and return result with metadata"""
        if not command.strip():
            return {"output": "", "error": "", "exit_code": 0, "command": command}
        
        self.command_history.append(command)
        
        try:
            # Handle special Windows commands
            if platform.system() == "Windows":
                command = self._handle_windows_commands(command)
            
            # Parse command and arguments
            parts = shlex.split(command)
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Check if it's a built-in command
            if cmd in self.built_in_commands:
                return self._execute_builtin(cmd, args, command)
            else:
                return self._execute_system_command(parts, command)
                
        except Exception as e:
            return {
                "output": "",
                "error": f"Error parsing command: {str(e)}",
                "exit_code": 1,
                "command": command
            }
    
    def _handle_windows_commands(self, command: str) -> str:
        """Handle Windows-specific command translations"""
        # Common Windows to Unix command translations
        translations = {
            'dir': 'ls',
            'type': 'cat',
            'del': 'rm',
            'copy': 'cp',
            'move': 'mv',
            'cls': 'clear'
        }
        
        parts = command.split()
        if parts and parts[0].lower() in translations:
            parts[0] = translations[parts[0].lower()]
            return ' '.join(parts)
        
        return command
    
    def _execute_builtin(self, cmd: str, args: List[str], original_command: str) -> Dict[str, Any]:
        """Execute built-in command"""
        try:
            result = self.built_in_commands[cmd](args)
            return {
                "output": result,
                "error": "",
                "exit_code": 0,
                "command": original_command
            }
        except Exception as e:
            return {
                "output": "",
                "error": str(e),
                "exit_code": 1,
                "command": original_command
            }
    
    def _execute_system_command(self, parts: List[str], original_command: str) -> Dict[str, Any]:
        """Execute system command"""
        try:
            # Execute in current directory
            result = subprocess.run(
                parts,
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                env=self.environment_vars,
                shell=True if platform.system() == "Windows" else False
            )
            
            return {
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode,
                "command": original_command
            }
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": "Command timed out after 30 seconds",
                "exit_code": 124,
                "command": original_command
            }
        except FileNotFoundError:
            return {
                "output": "",
                "error": f"Command not found: {parts[0]}",
                "exit_code": 127,
                "command": original_command
            }
        except Exception as e:
            return {
                "output": "",
                "error": f"Error executing command: {str(e)}",
                "exit_code": 1,
                "command": original_command
            }
    
    # Built-in command implementations
    def _cd(self, args: List[str]) -> str:
        if not args:
            # Go to home directory
            target = os.path.expanduser("~")
        else:
            target = args[0]
            if target.startswith("~"):
                target = os.path.expanduser(target)
            elif not os.path.isabs(target):
                target = os.path.join(self.current_dir, target)
        
        try:
            target = os.path.abspath(target)
            if os.path.isdir(target):
                os.chdir(target)
                self.current_dir = os.getcwd()
                return f"Changed directory to: {self.current_dir}"
            else:
                raise Exception(f"cd: '{target}' is not a directory")
        except OSError as e:
            raise Exception(f"cd: {str(e)}")
    
    def _pwd(self, args: List[str]) -> str:
        return self.current_dir
    
    def _ls(self, args: List[str]) -> str:
        # Handle flags
        show_all = '-a' in args or '--all' in args
        long_format = '-l' in args or '--long' in args
        
        # Remove flags to get path
        path_args = [arg for arg in args if not arg.startswith('-')]
        target = path_args[0] if path_args else self.current_dir
        
        if target.startswith("~"):
            target = os.path.expanduser(target)
        elif not os.path.isabs(target):
            target = os.path.join(self.current_dir, target)
        
        try:
            if os.path.isfile(target):
                return os.path.basename(target)
            elif os.path.isdir(target):
                items = os.listdir(target)
                if not show_all:
                    items = [item for item in items if not item.startswith('.')]
                
                items.sort()
                
                if long_format:
                    result = []
                    for item in items:
                        item_path = os.path.join(target, item)
                        try:
                            stat = os.stat(item_path)
                            size = stat.st_size
                            is_dir = os.path.isdir(item_path)
                            permissions = 'drwxr-xr-x' if is_dir else '-rw-r--r--'
                            result.append(f"{permissions} {size:8d} {item}")
                        except OSError:
                            result.append(f"?????????? {0:8d} {item}")
                    return '\n'.join(result)
                else:
                    return '  '.join(items)
            else:
                raise Exception(f"'{target}': No such file or directory")
        except OSError as e:
            raise Exception(f"ls: {str(e)}")
    
    def _mkdir(self, args: List[str]) -> str:
        if not args:
            raise Exception("mkdir: missing operand")
        
        created = []
        for arg in args:
            path = os.path.join(self.current_dir, arg) if not os.path.isabs(arg) else arg
            try:
                os.makedirs(path, exist_ok=False)
                created.append(arg)
            except OSError as e:
                if "File exists" in str(e):
                    raise Exception(f"mkdir: cannot create directory '{arg}': File exists")
                else:
                    raise Exception(f"mkdir: cannot create directory '{arg}': {str(e)}")
        
        return f"Created directories: {', '.join(created)}"
    
    def _rmdir(self, args: List[str]) -> str:
        if not args:
            raise Exception("rmdir: missing operand")
        
        removed = []
        for arg in args:
            path = os.path.join(self.current_dir, arg) if not os.path.isabs(arg) else arg
            try:
                os.rmdir(path)
                removed.append(arg)
            except OSError as e:
                raise Exception(f"rmdir: failed to remove '{arg}': {str(e)}")
        
        return f"Removed directories: {', '.join(removed)}"
    
    def _rm(self, args: List[str]) -> str:
        if not args:
            raise Exception("rm: missing operand")
        
        # Handle flags
        recursive = '-r' in args or '-rf' in args or '--recursive' in args
        force = '-f' in args or '-rf' in args or '--force' in args
        
        # Remove flags to get files
        files = [arg for arg in args if not arg.startswith('-')]
        
        if not files:
            raise Exception("rm: missing operand")
        
        removed = []
        for file_arg in files:
            path = os.path.join(self.current_dir, file_arg) if not os.path.isabs(file_arg) else file_arg
            
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    removed.append(file_arg)
                elif os.path.isdir(path):
                    if recursive:
                        shutil.rmtree(path)
                        removed.append(file_arg)
                    else:
                        raise Exception(f"rm: cannot remove '{file_arg}': Is a directory")
                elif not force:
                    raise Exception(f"rm: cannot remove '{file_arg}': No such file or directory")
            except OSError as e:
                if not force:
                    raise Exception(f"rm: cannot remove '{file_arg}': {str(e)}")
        
        if removed:
            return f"Removed: {', '.join(removed)}"
        else:
            return "No files removed"
    
    def _cp(self, args: List[str]) -> str:
        if len(args) < 2:
            raise Exception("cp: missing file operand")
        
        source = os.path.join(self.current_dir, args[0]) if not os.path.isabs(args[0]) else args[0]
        dest = os.path.join(self.current_dir, args[1]) if not os.path.isabs(args[1]) else args[1]
        
        try:
            if os.path.isdir(source):
                if os.path.exists(dest):
                    dest = os.path.join(dest, os.path.basename(source))
                shutil.copytree(source, dest)
            else:
                if os.path.isdir(dest):
                    dest = os.path.join(dest, os.path.basename(source))
                shutil.copy2(source, dest)
            return f"Copied '{args[0]}' to '{args[1]}'"
        except OSError as e:
            raise Exception(f"cp: {str(e)}")
    
    def _mv(self, args: List[str]) -> str:
        if len(args) < 2:
            raise Exception("mv: missing file operand")
        
        source = os.path.join(self.current_dir, args[0]) if not os.path.isabs(args[0]) else args[0]
        dest = os.path.join(self.current_dir, args[1]) if not os.path.isabs(args[1]) else args[1]
        
        try:
            if os.path.isdir(dest) and os.path.exists(dest):
                dest = os.path.join(dest, os.path.basename(source))
            shutil.move(source, dest)
            return f"Moved '{args[0]}' to '{args[1]}'"
        except OSError as e:
            raise Exception(f"mv: {str(e)}")
    
    def _cat(self, args: List[str]) -> str:
        if not args:
            raise Exception("cat: missing file operand")
        
        result = []
        for arg in args:
            path = os.path.join(self.current_dir, arg) if not os.path.isabs(arg) else arg
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if len(args) > 1:
                        result.append(f"==> {arg} <==\n{content}")
                    else:
                        result.append(content)
            except OSError as e:
                raise Exception(f"cat: {arg}: {str(e)}")
        
        return "\n".join(result)
    
    def _echo(self, args: List[str]) -> str:
        return " ".join(args)
    
    def _clear(self, args: List[str]) -> str:
        return "\033[2J\033[H"  # ANSI escape codes for clear screen
    
    def _exit(self, args: List[str]) -> str:
        sys.exit(0)
    
    def _history(self, args: List[str]) -> str:
        if not self.command_history:
            return "No commands in history"
        
        result = []
        for i, cmd in enumerate(self.command_history, 1):
            result.append(f"{i:4d}  {cmd}")
        return "\n".join(result)
    
    def _ps(self, args: List[str]) -> str:
        """Show running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append(f"{pinfo['pid']:>6} {pinfo['name']:<20} {pinfo['cpu_percent']:>6.1f}% {pinfo['memory_percent']:>6.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            header = f"{'PID':>6} {'NAME':<20} {'CPU%':>6} {'MEM%':>6}"
            return header + "\n" + "\n".join(processes[:20])  # Show top 20
        except Exception as e:
            return f"Error getting process list: {str(e)}"
    
    def _top(self, args: List[str]) -> str:
        """Show system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            result = [
                f"CPU Usage: {cpu_percent:.1f}%",
                f"Memory Usage: {memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)",
                "",
                "Top Processes:"
            ]
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append((pinfo['cpu_percent'], pinfo))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x[0], reverse=True)
            
            for cpu_pct, pinfo in processes[:10]:
                result.append(f"{pinfo['pid']:>6} {pinfo['name']:<20} {cpu_pct:>6.1f}% {pinfo['memory_percent']:>6.1f}%")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error getting system info: {str(e)}"
    
    def _df(self, args: List[str]) -> str:
        """Show disk space usage"""
        try:
            partitions = psutil.disk_partitions()
            result = [f"{'Filesystem':<20} {'Size':<10} {'Used':<10} {'Avail':<10} {'Use%':<6} {'Mounted on'}"]
            
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    result.append(f"{partition.device:<20} "
                                f"{partition_usage.total // (1024**3):>8}GB "
                                f"{partition_usage.used // (1024**3):>8}GB "
                                f"{partition_usage.free // (1024**3):>8}GB "
                                f"{partition_usage.percent:>5.1f}% "
                                f"{partition.mountpoint}")
                except PermissionError:
                    continue
            
            return "\n".join(result)
        except Exception as e:
            return f"Error getting disk info: {str(e)}"
    
    def _free(self, args: List[str]) -> str:
        """Show memory usage"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            result = [
                f"{'Type':<12} {'Total':<12} {'Used':<12} {'Free':<12} {'Available':<12}",
                f"{'Memory':<12} {memory.total // (1024**2):>10}MB {memory.used // (1024**2):>10}MB "
                f"{memory.free // (1024**2):>10}MB {memory.available // (1024**2):>10}MB",
                f"{'Swap':<12} {swap.total // (1024**2):>10}MB {swap.used // (1024**2):>10}MB "
                f"{swap.free // (1024**2):>10}MB {0:>10}MB"
            ]
            
            return "\n".join(result)
        except Exception as e:
            return f"Error getting memory info: {str(e)}"
    
    def _whoami(self, args: List[str]) -> str:
        return os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    
    def _env(self, args: List[str]) -> str:
        if args:
            var_name = args[0]
            return self.environment_vars.get(var_name, f"Environment variable '{var_name}' not found")
        else:
            result = []
            for key, value in sorted(self.environment_vars.items()):
                result.append(f"{key}={value}")
            return "\n".join(result[:50])  # Limit to first 50 for readability
    
    def _export(self, args: List[str]) -> str:
        if not args:
            raise Exception("export: missing variable assignment")
        
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                self.environment_vars[key] = value
                os.environ[key] = value
            else:
                raise Exception(f"export: invalid assignment '{arg}'")
        
        return f"Exported variables: {', '.join(args)}"
    
    def _find(self, args: List[str]) -> str:
        if not args:
            pattern = "*"
            search_path = self.current_dir
        else:
            pattern = args[-1]
            search_path = args[0] if len(args) > 1 else self.current_dir
        
        if not os.path.isabs(search_path):
            search_path = os.path.join(self.current_dir, search_path)
        
        matches = []
        try:
            for root, dirs, files in os.walk(search_path):
                for name in dirs + files:
                    if pattern == "*" or pattern in name:
                        matches.append(os.path.join(root, name))
        except Exception as e:
            return f"Error during search: {str(e)}"
        
        return "\n".join(matches) if matches else "No matches found"
    
    def _grep(self, args: List[str]) -> str:
        if len(args) < 2:
            raise Exception("grep: missing pattern or file")
        
        pattern = args[0]
        files = args[1:]
        result = []
        
        for file in files:
            path = os.path.join(self.current_dir, file) if not os.path.isabs(file) else file
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            prefix = f"{file}:" if len(files) > 1 else ""
                            result.append(f"{prefix}{line_num}:{line.rstrip()}")
            except OSError as e:
                result.append(f"grep: {file}: {str(e)}")
        
        return "\n".join(result) if result else f"No matches found for '{pattern}'"
    
    def _touch(self, args: List[str]) -> str:
        if not args:
            raise Exception("touch: missing file operand")
        
        created = []
        for arg in args:
            path = os.path.join(self.current_dir, arg) if not os.path.isabs(arg) else arg
            try:
                Path(path).touch()
                created.append(arg)
            except OSError as e:
                raise Exception(f"touch: cannot touch '{arg}': {str(e)}")
        
        return f"Touched files: {', '.join(created)}"
    
    def _help(self, args: List[str]) -> str:
        help_text = """
Built-in Commands:
  cd [dir]         - Change directory
  pwd              - Print working directory  
  ls [dir]         - List directory contents
  mkdir <dir>      - Create directory
  rmdir <dir>      - Remove empty directory
  rm <file/dir>    - Remove file or directory
  cp <src> <dest>  - Copy file or directory
  mv <src> <dest>  - Move/rename file or directory
  cat <file>       - Display file contents
  echo <text>      - Display text
  clear/cls        - Clear screen
  history          - Show command history
  ps               - Show running processes
  top              - Show system resources and top processes
  df               - Show disk space usage
  free             - Show memory usage
  whoami           - Show current user
  env [var]        - Show environment variables
  export var=val   - Set environment variable
  find [dir] <pattern> - Find files matching pattern
  grep <pattern> <files> - Search for pattern in files
  touch <file>     - Create empty file or update timestamp
  help             - Show this help message
  exit             - Exit terminal

Command aliases:
  list             - Same as 'ls'
  show/display     - Same as 'cat'
  create           - Same as 'touch'
  delete/remove    - Same as 'rm'

System commands are also supported and executed in the current directory.
        """
        return help_text.strip()
    
    def get_current_directory(self) -> str:
        return self.current_dir
    
    def get_prompt(self) -> str:
        user = os.getenv('USER', os.getenv('USERNAME', 'user'))
        hostname = platform.node()
        return f"{user}@{hostname}:{os.path.basename(self.current_dir)}$ "
    
    @property
    def current_directory(self):
        return self.current_dir