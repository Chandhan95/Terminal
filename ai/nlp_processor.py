import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Command:
    """Represents a parsed command"""
    action: str
    target: str
    options: List[str] = None
    source: str = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []

class NLPProcessor:
    """
    Natural Language Processing for terminal commands
    Converts natural language queries to actual terminal commands
    """
    
    def __init__(self):
        self.action_patterns = self._build_action_patterns()
        self.file_operations = self._build_file_operations()
        self.navigation_patterns = self._build_navigation_patterns()
        self.system_patterns = self._build_system_patterns()
    
    def _build_action_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for different actions"""
        return {
            'create': [
                r'create (a )?new (file|folder|directory) (called|named) ([^\s]+)',
                r'make (a )?new (file|folder|directory) ([^\s]+)',
                r'touch (file )?([^\s]+)',
                r'mkdir ([^\s]+)'
            ],
            'delete': [
                r'delete (the )?(file|folder|directory) ([^\s]+)',
                r'remove (the )?(file|folder|directory) ([^\s]+)',
                r'rm ([^\s]+)',
                r'delete ([^\s]+)'
            ],
            'copy': [
                r'copy (the )?(file|folder) ([^\s]+) to ([^\s]+)',
                r'copy ([^\s]+) to ([^\s]+)',
                r'cp ([^\s]+) ([^\s]+)'
            ],
            'move': [
                r'move (the )?(file|folder) ([^\s]+) to ([^\s]+)',
                r'move ([^\s]+) to ([^\s]+)',
                r'mv ([^\s]+) ([^\s]+)',
                r'rename ([^\s]+) to ([^\s]+)'
            ],
            'list': [
                r'list (all )?(files|contents) (in )?([^\s]*)',
                r'show (me )?(all )?(files|contents) (in )?([^\s]*)',
                r'ls ([^\s]*)',
                r'what\'?s in ([^\s]+)',
                r'list (files|contents)',
                r'show (files|contents)'
            ],
            'navigate': [
                r'go to (the )?(folder|directory) ([^\s]+)',
                r'change to (the )?(folder|directory) ([^\s]+)',
                r'cd ([^\s]+)',
                r'navigate to ([^\s]+)'
            ],
            'view': [
                r'show (me )?(the )?(contents of )?([^\s]+)',
                r'read (the )?(file )?([^\s]+)',
                r'cat ([^\s]+)',
                r'display ([^\s]+)'
            ]
        }
    
    def _build_file_operations(self) -> Dict[str, str]:
        """Map file operations to commands"""
        return {
            'create_file': 'touch {}',
            'create_directory': 'mkdir {}',
            'delete_file': 'rm {}',
            'delete_directory': 'rm -rf {}',
            'copy': 'cp {} {}',
            'move': 'mv {} {}',
            'list': 'ls {}',
            'view': 'cat {}',
            'navigate': 'cd {}'
        }
    
    def _build_navigation_patterns(self) -> Dict[str, str]:
        """Build navigation patterns"""
        return {
            'home': r'go (to )?home|cd home|go (to )?~',
            'parent': r'go (to )?parent|go up|cd \.\.',
            'root': r'go (to )?root|cd /'
        }
    
    def _build_system_patterns(self) -> Dict[str, str]:
        """Build system command patterns"""
        return {
            'processes': r'show (me )?(running )?processes|list processes|ps',
            'system_info': r'show (me )?system info|system information|systeminfo',
            'disk_space': r'show (me )?disk space|disk usage|df',
            'memory': r'show (me )?memory usage|memory info|free',
            'top': r'show (me )?top processes|top',
            'current_directory': r'where am i|current directory|pwd',
            'current_user': r'who am i|current user|whoami',
            'date_time': r'what time is it|current date|date'
        }
    
    def process_natural_language(self, query: str) -> str:
        """
        Process natural language query and convert to terminal command
        """
        query = query.lower().strip()
        
        # Check for compound commands (using 'and' or ';')
        if ' and ' in query or ';' in query:
            return self._process_compound_command(query)
        
        # Try to match system commands first
        system_command = self._match_system_command(query)
        if system_command:
            return system_command
        
        # Try to match navigation commands
        nav_command = self._match_navigation_command(query)
        if nav_command:
            return nav_command
        
        # Try to match file operations
        file_command = self._match_file_operation(query)
        if file_command:
            return file_command
        
        # If no patterns match, suggest possibilities
        return self._suggest_command(query)
    
    def _process_compound_command(self, query: str) -> str:
        """Process compound commands separated by 'and' or ';'"""
        # Split by 'and' or ';'
        parts = re.split(r'\s+and\s+|;', query)
        commands = []
        
        for part in parts:
            part = part.strip()
            cmd = self.process_natural_language(part)
            if not cmd.startswith("I'm not sure"):
                commands.append(cmd)
        
        return ' && '.join(commands) if commands else "Could not parse compound command"
    
    def _match_system_command(self, query: str) -> Optional[str]:
        """Match system commands"""
        for command, pattern in self.system_patterns.items():
            if re.search(pattern, query):
                command_map = {
                    'processes': 'ps',
                    'system_info': 'systeminfo',
                    'disk_space': 'df',
                    'memory': 'free',
                    'top': 'top',
                    'current_directory': 'pwd',
                    'current_user': 'whoami',
                    'date_time': 'date'
                }
                return command_map.get(command, command)
        return None
    
    def _match_navigation_command(self, query: str) -> Optional[str]:
        """Match navigation commands"""
        for command, pattern in self.navigation_patterns.items():
            if re.search(pattern, query):
                nav_map = {
                    'home': 'cd ~',
                    'parent': 'cd ..',
                    'root': 'cd /'
                }
                return nav_map.get(command)
        return None
    
    def _match_file_operation(self, query: str) -> Optional[str]:
        """Match file operations"""
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return self._build_command(action, match.groups())
        return None
    
    def _build_command(self, action: str, groups: Tuple) -> str:
        """Build terminal command from action and regex groups"""
        if action == 'create':
            if len(groups) >= 4:
                file_type = groups[1]  # file or folder/directory
                name = groups[3]
                if file_type == 'file':
                    return f'touch {name}'
                else:
                    return f'mkdir {name}'
            elif len(groups) >= 2:
                return f'touch {groups[1]}'  # Default to file creation
        
        elif action == 'delete':
            if len(groups) >= 3:
                return f'rm {groups[2]}'
            elif len(groups) >= 1:
                return f'rm {groups[0]}'
        
        elif action == 'copy':
            if len(groups) >= 4:
                return f'cp {groups[2]} {groups[3]}'
            elif len(groups) >= 2:
                return f'cp {groups[0]} {groups[1]}'
        
        elif action == 'move':
            if len(groups) >= 4:
                return f'mv {groups[2]} {groups[3]}'
            elif len(groups) >= 2:
                return f'mv {groups[0]} {groups[1]}'
        
        elif action == 'list':
            if len(groups) >= 4 and groups[3]:
                return f'ls {groups[3]}'
            elif len(groups) >= 1 and groups[0]:
                return f'ls {groups[0]}'
            else:
                return 'ls'
        
        elif action == 'navigate':
            if len(groups) >= 3:
                return f'cd {groups[2]}'
            elif len(groups) >= 1:
                return f'cd {groups[0]}'
        
        elif action == 'view':
            if len(groups) >= 4:
                return f'cat {groups[3]}'
            elif len(groups) >= 1:
                return f'cat {groups[0]}'
        
        return f"# Could not build command for action: {action}"
    
    def _suggest_command(self, query: str) -> str:
        """Suggest possible commands when no pattern matches"""
        # Extract potential filenames or operations
        words = query.split()
        
        suggestions = []
        
        # Look for file-like words
        for word in words:
            if '.' in word or word.endswith('/'):
                suggestions.append(f"Did you mean: ls {word} or cat {word}?")
        
        # Look for action words
        action_keywords = {
            'show': 'ls or cat',
            'find': 'find or locate',
            'search': 'grep or find',
            'install': 'This terminal doesn\'t support package installation',
            'download': 'Use wget or curl',
            'edit': 'vim or nano'
        }
        
        for word in words:
            if word in action_keywords:
                suggestions.append(f"For '{word}', try: {action_keywords[word]}")
        
        if suggestions:
            return "I'm not sure about that command. " + " ".join(suggestions)
        else:
            return f"I'm not sure how to interpret '{query}'. Try using specific commands like 'ls', 'cd', 'cat', etc., or ask for 'help'."
    
    def get_help_text(self) -> str:
        """Get help text for natural language commands"""
        return """Natural Language Command Examples:

File Operations:
- "create a new file called test.txt"
- "make a new folder documents"
- "delete the file old.txt"
- "copy file1.txt to backup.txt"
- "move data.csv to archive folder"

Navigation:
- "go to the documents folder"
- "navigate to /home/user"
- "go home"
- "go to parent directory"

Viewing:
- "show me the contents of config.txt"
- "list all files in documents"
- "what's in the current directory"

System Info:
- "show me running processes"
- "show system information"
- "show disk space"
- "show memory usage"

You can also combine commands:
- "create a new folder test and navigate to it"
- "copy file1.txt to backup.txt and delete the original"
"""

class AITerminal:
    """
    Enhanced terminal with AI natural language processing
    This class acts as a wrapper around the base terminal, adding AI capabilities
    """
    
    def __init__(self, base_terminal):
        self.base_terminal = base_terminal
        self.nlp_processor = NLPProcessor()
        
        # Add AI commands to base terminal
        self.base_terminal.built_in_commands.update({
            'ai_help': lambda args: self.nlp_processor.get_help_text(),
            'ask': self._process_natural_language_command
        })
    
    def _process_natural_language_command(self, args: List[str]) -> str:
        """Process natural language command"""
        if not args:
            return "Please provide a natural language command. Example: ask 'create a new file called test.txt'"
        
        # Join all arguments to form the query
        query = ' '.join(args)
        
        # Remove quotes if present
        query = query.strip('"\'')
        
        # Process the query
        command = self.nlp_processor.process_natural_language(query)
        
        # Execute the generated command
        if not command.startswith("I'm not sure") and not command.startswith("#"):
            print(f"Executing: {command}")
            result = self.base_terminal.execute_command(command)
            
            if result['output']:
                return result['output']
            elif result['error']:
                return f"Error: {result['error']}"
            else:
                return "Command executed successfully"
        else:
            return command
    
    def execute_command(self, command_line: str):
        """Execute command with AI preprocessing"""
        # Check if this might be a natural language query
        if self._is_natural_language(command_line):
            # Try to process as natural language
            interpreted_command = self.nlp_processor.process_natural_language(command_line)
            
            if not interpreted_command.startswith("I'm not sure"):
                print(f"Interpreted as: {interpreted_command}")
                return self.base_terminal.execute_command(interpreted_command)
        
        # Execute normally
        return self.base_terminal.execute_command(command_line)
    
    def _is_natural_language(self, command: str) -> bool:
        """Heuristic to determine if command is natural language"""
        # Check for natural language indicators
        natural_indicators = [
            'create a', 'make a', 'show me', 'list all', 'go to',
            'what is', 'how do', 'can you', 'please', 'could you'
        ]
        
        command_lower = command.lower()
        for indicator in natural_indicators:
            if indicator in command_lower:
                return True
        
        # Check if command has spaces and doesn't start with known commands
        known_commands = list(self.base_terminal.built_in_commands.keys())
        first_word = command.split()[0].lower()
        
        return len(command.split()) > 2 and first_word not in known_commands
    
    # Delegate all other methods to the base terminal
    def __getattr__(self, name):
        """Delegate any missing methods to the base terminal"""
        return getattr(self.base_terminal, name)
    
    # Explicitly expose important methods for clarity
    def get_prompt(self):
        """Get the terminal prompt"""
        return self.base_terminal.get_prompt()
    
    def get_current_directory(self):
        """Get current directory"""
        return self.base_terminal.get_current_directory()
    
    @property
    def current_directory(self):
        """Get current directory as property"""
        return self.base_terminal.current_directory
    
    @property
    def command_history(self):
        """Get command history"""
        return self.base_terminal.command_history
    
    @property
    def built_in_commands(self):
        """Get built-in commands"""
        return self.base_terminal.built_in_commands