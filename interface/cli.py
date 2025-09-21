import os
import sys
import signal
import psutil
from typing import List, Optional
import atexit
import socket

# Import our terminal components
from core.terminal import PythonTerminal
from core.system_monitor import SystemMonitor, command_top, command_free, command_df, command_uptime, command_systeminfo

# Try to import readline for command history
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    try:
        import pyreadline3 as readline  # Windows alternative
        READLINE_AVAILABLE = True
    except ImportError:
        READLINE_AVAILABLE = False

class CLIInterface:
    """
    Command Line Interface for the Python Terminal
    """
    
    def __init__(self):
        self.terminal = PythonTerminal()
        self.running = True
        if READLINE_AVAILABLE:
            self.setup_readline()
        self.register_additional_commands()
        self.setup_signal_handlers()
    
    def setup_readline(self):
        """Setup readline for command history and auto-completion"""
        # History file
        histfile = os.path.join(os.path.expanduser("~"), ".python_terminal_history")
        
        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        except Exception:
            # Handle any readline issues gracefully
            pass
        
        # Save history on exit
        atexit.register(self._save_history, histfile)
        
        # Setup tab completion
        readline.set_completer(self.complete)
        readline.parse_and_bind('tab: complete')
    
    def _save_history(self, histfile):
        """Save command history"""
        try:
            readline.write_history_file(histfile)
        except Exception:
            pass  # Fail silently if we can't save history
    
    def register_additional_commands(self):
        """Register additional system monitoring commands"""
        self.terminal.built_in_commands.update({
            'top': lambda args: command_top(args),
            'free': lambda args: command_free(args),
            'df': lambda args: command_df(args),
            'uptime': lambda args: command_uptime(args),
            'systeminfo': lambda args: command_systeminfo(args),
        })
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            if signum == signal.SIGINT:
                print("\n^C")
                return
            elif signum == signal.SIGTERM:
                print("\nTerminal shutting down...")
                self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def complete(self, text: str, state: int) -> Optional[str]:
        """Tab completion handler"""
        if not READLINE_AVAILABLE:
            return None
            
        if state == 0:
            self.matches = []
            line = readline.get_line_buffer()
            words = line.split()
            
            if not words or (len(words) == 1 and not line.endswith(' ')):
                # Complete command names
                commands = list(self.terminal.built_in_commands.keys())
                system_commands = ['grep', 'find', 'locate', 'which', 'man', 'vim', 'nano', 'less', 'more']
                all_commands = commands + system_commands
                self.matches = [cmd for cmd in all_commands if cmd.startswith(text)]
            else:
                # Complete file/directory names
                self.matches = self.complete_path(text)
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def complete_path(self, text: str) -> List[str]:
        """Complete file and directory paths"""
        if not text:
            path = self.terminal.current_directory
            prefix = ""
        else:
            if text.startswith('/'):
                # Absolute path
                if text.endswith('/'):
                    path = text
                    prefix = text
                else:
                    path = os.path.dirname(text)
                    prefix = os.path.dirname(text) + '/'
                    if prefix == '/':
                        prefix = '/'
            else:
                # Relative path
                if '/' in text:
                    rel_path = os.path.dirname(text)
                    path = os.path.join(self.terminal.current_directory, rel_path)
                    prefix = rel_path + '/'
                else:
                    path = self.terminal.current_directory
                    prefix = ""
        
        matches = []
        try:
            if os.path.isdir(path):
                for item in os.listdir(path):
                    if item.startswith(os.path.basename(text)):
                        if os.path.isdir(os.path.join(path, item)):
                            matches.append(prefix + item + '/')
                        else:
                            matches.append(prefix + item)
        except (OSError, PermissionError):
            pass
        
        return matches
    
    def print_welcome(self):
        """Print welcome message"""
        print("=" * 60)
        print("  Python Terminal v2.0")
        print("  Type 'help' for available commands")
        print("  Type 'exit' to quit")
        if not READLINE_AVAILABLE:
            print("  (Command history disabled - readline not available)")
        print("=" * 60)
        print()
    
    def run(self):
        """Main CLI loop"""
        self.print_welcome()
        
        while self.running:
            try:
                # Get and display prompt
                prompt = self.terminal.get_prompt()
                
                # Read command
                try:
                    command_line = input(prompt)
                except EOFError:
                    print("\nGoodbye!")
                    break
                except KeyboardInterrupt:
                    print("^C")
                    continue
                
                if not command_line.strip():
                    continue
                
                # Execute command
                result = self.terminal.execute_command(command_line)
                
                # Handle special cases
                if result["output"] == "CLEAR_SCREEN":
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                
                # Display output
                if result["output"]:
                    print(result["output"])
                
                # Display errors
                if result["error"]:
                    print(f"Error: {result['error']}", file=sys.stderr)
                
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)
                continue
        
        print("Terminal session ended.")

class WebInterface:
    """
    Web-based interface for the terminal
    """
    
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.terminal = PythonTerminal()
        self._find_available_port()
    
    def _find_available_port(self):
        """Find an available port if the default is in use"""
        def is_port_available(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self.host, port))
                    return True
                except OSError:
                    return False
        
        # Try the specified port first
        if is_port_available(self.port):
            return
        
        # Try alternative ports
        alternative_ports = [5000, 5001, 8000, 8001, 8080, 8888, 9000]
        for port in alternative_ports:
            if port != self.port and is_port_available(port):
                print(f"Port {self.port} is in use, switching to port {port}")
                self.port = port
                return
        
        # If no alternatives work, we'll let Flask handle the error
        print(f"Warning: Port {self.port} may be in use. Will attempt to start anyway.")
    
    def create_app(self):
        """Create Flask web application"""
        try:
            from flask import Flask, render_template_string, request, jsonify
        except ImportError:
            raise ImportError("Flask is required for web interface. Install with: pip install flask")
        
        app = Flask(__name__)
        
        # HTML template embedded in Python (since we don't have a templates folder by default)
        TERMINAL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Terminal - Web Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #00ff00;
            height: 100vh;
            overflow: hidden;
        }
        
        .terminal-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        .terminal-header {
            background: #333;
            padding: 10px 15px;
            border-radius: 5px 5px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .terminal-title {
            color: #fff;
            font-weight: bold;
        }
        
        .terminal-controls {
            display: flex;
            gap: 10px;
        }
        
        .control-btn {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }
        
        .close { background: #ff5f56; }
        .minimize { background: #ffbd2e; }
        .maximize { background: #27ca3f; }
        
        .terminal-output {
            flex: 1;
            background: #000;
            padding: 15px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .terminal-input-container {
            background: #000;
            padding: 15px;
            border-top: 1px solid #333;
            display: flex;
            align-items: center;
        }
        
        .terminal-prompt {
            color: #00ff00;
            margin-right: 10px;
            min-width: fit-content;
        }
        
        .terminal-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #00ff00;
            font-family: inherit;
            font-size: 14px;
            outline: none;
        }
        
        .command-line {
            margin-bottom: 5px;
        }
        
        .command-prompt {
            color: #00ff00;
        }
        
        .command-text {
            color: #fff;
        }
        
        .output-text {
            color: #00ff00;
        }
        
        .error-text {
            color: #ff6b6b;
        }
        
        .system-info {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            max-width: 200px;
            display: none;
            z-index: 1000;
        }
        
        .toggle-info {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #333;
            color: #fff;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            z-index: 1001;
        }
        
        .loading {
            opacity: 0.7;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        .cursor {
            animation: blink 1s infinite;
            color: #00ff00;
        }
    </style>
</head>
<body>
    <div class="terminal-container">
        <div class="terminal-header">
            <div class="terminal-title">Python Terminal v2.0 - Web Interface</div>
            <div class="terminal-controls">
                <button class="control-btn close" onclick="closeTerminal()"></button>
                <button class="control-btn minimize" onclick="minimizeTerminal()"></button>
                <button class="control-btn maximize" onclick="maximizeTerminal()"></button>
            </div>
        </div>
        
        <div class="terminal-output" id="output">
            <div class="command-line">
                <span class="output-text">Python Terminal v2.0 - Web Interface</span>
            </div>
            <div class="command-line">
                <span class="output-text">Type 'help' for available commands</span>
            </div>
            <div class="command-line">
                <span class="output-text">AI features: {{ 'ENABLED' if ai_enabled else 'DISABLED' }}</span>
            </div>
            <div class="command-line">
                <span class="output-text">====================================</span>
            </div>
        </div>
        
        <div class="terminal-input-container">
            <span class="terminal-prompt" id="prompt">user@localhost:~$ </span>
            <input type="text" class="terminal-input" id="input" autocomplete="off" spellcheck="false">
            <span class="cursor">|</span>
        </div>
    </div>
    
    <button class="toggle-info" onclick="toggleSystemInfo()">System Info</button>
    
    <div class="system-info" id="systemInfo">
        <div id="systemInfoContent">Loading...</div>
    </div>

    <script>
        class WebTerminal {
            constructor() {
                this.output = document.getElementById('output');
                this.input = document.getElementById('input');
                this.prompt = document.getElementById('prompt');
                this.commandHistory = [];
                this.historyIndex = -1;
                
                this.setupEventListeners();
                this.loadSystemInfo();
                this.focusInput();
            }
            
            setupEventListeners() {
                this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
                document.addEventListener('click', () => this.focusInput());
            }
            
            handleKeyDown(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.executeCommand();
                } else if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    this.navigateHistory('up');
                } else if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    this.navigateHistory('down');
                } else if (event.key === 'Tab') {
                    event.preventDefault();
                    // TODO: Implement tab completion
                } else if (event.ctrlKey && event.key === 'l') {
                    event.preventDefault();
                    this.clearScreen();
                } else if (event.ctrlKey && event.key === 'c') {
                    event.preventDefault();
                    this.interruptCommand();
                }
            }
            
            async executeCommand() {
                const command = this.input.value.trim();
                
                if (!command) return;
                
                this.commandHistory.unshift(command);
                this.historyIndex = -1;
                
                this.addOutput(`<span class="command-prompt">${this.prompt.textContent}</span><span class="command-text">${command}</span>`);
                
                this.input.value = '';
                this.input.classList.add('loading');
                
                try {
                    const response = await fetch('/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ command: command })
                    });
                    
                    const result = await response.json();
                    
                    if (result.prompt) {
                        this.prompt.textContent = result.prompt;
                    }
                    
                    if (result.output) {
                        if (result.output === 'CLEAR_SCREEN') {
                            this.clearScreen();
                        } else {
                            this.addOutput(`<span class="output-text">${this.escapeHtml(result.output)}</span>`);
                        }
                    }
                    
                    if (result.error) {
                        this.addOutput(`<span class="error-text">Error: ${this.escapeHtml(result.error)}</span>`);
                    }
                    
                } catch (error) {
                    this.addOutput(`<span class="error-text">Connection error: ${error.message}</span>`);
                } finally {
                    this.input.classList.remove('loading');
                    this.focusInput();
                }
            }
            
            addOutput(content) {
                const line = document.createElement('div');
                line.className = 'command-line';
                line.innerHTML = content;
                this.output.appendChild(line);
                this.scrollToBottom();
            }
            
            navigateHistory(direction) {
                if (this.commandHistory.length === 0) return;
                
                if (direction === 'up') {
                    if (this.historyIndex < this.commandHistory.length - 1) {
                        this.historyIndex++;
                    }
                } else if (direction === 'down') {
                    if (this.historyIndex > 0) {
                        this.historyIndex--;
                    } else {
                        this.historyIndex = -1;
                        this.input.value = '';
                        return;
                    }
                }
                
                this.input.value = this.commandHistory[this.historyIndex] || '';
                setTimeout(() => {
                    this.input.setSelectionRange(this.input.value.length, this.input.value.length);
                }, 0);
            }
            
            clearScreen() {
                this.output.innerHTML = '<div class="command-line"><span class="output-text">Terminal cleared</span></div>';
            }
            
            interruptCommand() {
                this.addOutput('<span class="error-text">^C</span>');
                this.input.value = '';
            }
            
            scrollToBottom() {
                this.output.scrollTop = this.output.scrollHeight;
            }
            
            focusInput() {
                this.input.focus();
            }
            
            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML.replace(/\\n/g, '<br>').replace(/\\s/g, '&nbsp;');
            }
            
            async loadSystemInfo() {
                try {
                    const response = await fetch('/system_info');
                    const data = await response.json();
                    
                    const systemInfoContent = document.getElementById('systemInfoContent');
                    systemInfoContent.innerHTML = `
                        <strong>System:</strong> ${data.system.platform}<br>
                        <strong>CPU:</strong> ${data.cpu.total_cpu_usage}%<br>
                        <strong>Memory:</strong> ${data.memory.memory_percentage}%<br>
                        <strong>Cores:</strong> ${data.cpu.total_cores}<br>
                    `;
                } catch (error) {
                    console.error('Failed to load system info:', error);
                }
            }
        }
        
        function closeTerminal() {
            if (confirm('Are you sure you want to close the terminal?')) {
                window.close();
            }
        }
        
        function minimizeTerminal() {
            alert('Minimize not available in web interface');
        }
        
        function maximizeTerminal() {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                document.documentElement.requestFullscreen();
            }
        }
        
        function toggleSystemInfo() {
            const systemInfo = document.getElementById('systemInfo');
            const button = document.querySelector('.toggle-info');
            
            if (systemInfo.style.display === 'block') {
                systemInfo.style.display = 'none';
                button.textContent = 'System Info';
            } else {
                systemInfo.style.display = 'block';
                button.textContent = 'Hide Info';
                terminal.loadSystemInfo();
            }
        }
        
        let terminal;
        window.addEventListener('DOMContentLoaded', () => {
            terminal = new WebTerminal();
        });
        
        document.addEventListener('contextmenu', (e) => {
            if (e.target.closest('.terminal-container')) {
                e.preventDefault();
            }
        });
        
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                terminal.focusInput();
            }
        });
    </script>
</body>
</html>'''
        
        @app.route('/')
        def index():
            ai_enabled = hasattr(self.terminal, 'nlp_processor')
            return render_template_string(TERMINAL_HTML, ai_enabled=ai_enabled)
        
        @app.route('/execute', methods=['POST'])
        def execute_command():
            command = request.json.get('command', '')
            result = self.terminal.execute_command(command)
            
            # Add current directory to response
            result['cwd'] = self.terminal.current_directory
            result['prompt'] = self.terminal.get_prompt()
            
            return jsonify(result)
        
        @app.route('/system_info')
        def system_info():
            return jsonify({
                'cpu': SystemMonitor.get_cpu_info(),
                'memory': SystemMonitor.get_memory_info(),
                'disk': SystemMonitor.get_disk_info(),
                'network': SystemMonitor.get_network_info(),
                'system': SystemMonitor.get_system_info()
            })
        
        return app
    
    def run(self):
        """Run the web interface"""
        app = self.create_app()
        print(f"Starting web terminal at http://{self.host}:{self.port}")
        
        # Configure Flask to be less verbose
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
        
        try:
            app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except OSError as e:
            if "address already in use" in str(e).lower() or "access is denied" in str(e).lower():
                print(f"Error: Port {self.port} is not available.")
                print("This could be because:")
                print("1. Another application is using the port")
                print("2. Windows Firewall is blocking the port")
                print("3. You need administrator privileges")
                print(f"\nTry using a different port: python main.py --web --port 8888")
                print("Or run as administrator if needed.")
            else:
                print(f"Web interface error: {e}")

def main():
    """Main entry point for CLI/Web interfaces"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python Terminal Interface')
    parser.add_argument('--web', action='store_true', help='Run web interface')
    parser.add_argument('--host', default='localhost', help='Web interface host')
    parser.add_argument('--port', type=int, default=5000, help='Web interface port')
    
    args = parser.parse_args()
    
    if args.web:
        web_interface = WebInterface(args.host, args.port)
        web_interface.run()
    else:
        cli_interface = CLIInterface()
        cli_interface.run()

if __name__ == "__main__":
    main()