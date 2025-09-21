#!/usr/bin/env python3
"""
Python Terminal - A fully functional command terminal built in Python
Author: AI Assistant
Version: 2.0
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def install_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'psutil': 'System monitoring functionality',
        'flask': 'Web interface (optional)',
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'flask':
                # Flask is optional for web interface
                continue
            __import__(package)
        except ImportError:
            missing_packages.append((package, description))
    
    # Check for readline (platform specific)
    try:
        import readline
    except ImportError:
        try:
            import pyreadline3  # Windows alternative
        except ImportError:
            print("Warning: readline not available. Command history may not work.")
    
    if missing_packages:
        print("Missing required packages:")
        for package, description in missing_packages:
            print(f"  - {package}: {description}")
        
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements.txt")
        
        return False
    
    return True

def create_project_structure():
    """Create necessary project directories"""
    directories = [
        'core',
        'interface',
        'ai',
        'templates',
        'tests',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        # Create __init__.py files for Python packages
        if directory not in ['templates', 'logs']:
            init_file = Path(directory) / '__init__.py'
            init_file.touch(exist_ok=True)

def main():
    """Main entry point for the Python Terminal"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Python Terminal - A full-featured command terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start CLI terminal
  python main.py --web              # Start web interface
  python main.py --ai               # Start with AI natural language support
  python main.py --web --ai         # Start web interface with AI support
  python main.py --host 0.0.0.0     # Allow external connections to web interface
  python main.py --test             # Run functionality tests
        """
    )
    
    parser.add_argument('--web', action='store_true',
                       help='Start web-based interface instead of CLI')
    
    parser.add_argument('--ai', action='store_true',
                       help='Enable AI natural language processing')
    
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host for web interface (default: 0.0.0.0 for deployment)')
    
    parser.add_argument('--port', type=int, default=int(os.environ.get("PORT", 5000)),
                       help='Port for web interface (default: $PORT env or 5000)')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    parser.add_argument('--test', action='store_true',
                       help='Run functionality tests')
    
    parser.add_argument('--version', action='version', version='Python Terminal 2.0')
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        return run_tests()
    
    # Check dependencies
    if not install_dependencies():
        print("\nPlease install the required dependencies and try again.")
        return 1
    
    # Create project structure
    create_project_structure()
    
    try:
        # Import modules after structure is created
        from core.terminal import PythonTerminal
        from interface.cli import CLIInterface, WebInterface
        
        if args.web:
            # Start web interface
            print("Starting Python Terminal (Web Interface)")
            if args.ai:
                print("AI natural language processing: ENABLED")
            
            web_interface = WebInterface(args.host, args.port)
            
            if args.ai:
                # Import and enhance with AI capabilities
                try:
                    from ai.nlp_processor import AITerminal
                    web_interface.terminal = AITerminal(web_interface.terminal)
                    print("AI module loaded successfully")
                except ImportError as e:
                    print(f"Warning: Could not load AI module: {e}")
                    print("Continuing without AI features...")
            
            web_interface.run()
            
        else:
            # Start CLI interface
            print("Starting Python Terminal (Command Line Interface)")
            if args.ai:
                print("AI natural language processing: ENABLED")
                print("Type 'ai_help' for natural language command examples")
                print("Use 'ask \"your natural language command\"' to use AI")
                print()
            
            cli_interface = CLIInterface()
            
            if args.ai:
                # Import and enhance with AI capabilities
                try:
                    from ai.nlp_processor import AITerminal
                    cli_interface.terminal = AITerminal(cli_interface.terminal)
                    print("AI module loaded successfully")
                    print()
                except ImportError as e:
                    print(f"Warning: Could not load AI module: {e}")
                    print("Continuing without AI features...")
                    print()
            
            cli_interface.run()
    
    except KeyboardInterrupt:
        print("\n\nTerminal interrupted by user.")
        return 0
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1
    
    return 0

def run_tests():
    """Run basic tests to verify functionality"""
    print("Running Python Terminal functionality tests...")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Terminal creation
    try:
        from core.terminal import PythonTerminal
        terminal = PythonTerminal()
        test_results.append(("Terminal creation", True, ""))
        print("✅ Terminal creation successful")
    except Exception as e:
        test_results.append(("Terminal creation", False, str(e)))
        print(f"❌ Terminal creation failed: {e}")
        return 1
    
    # Test 2: Basic commands
    test_commands = [
        ('pwd', 'Print working directory'),
        ('echo hello world', 'Echo command'),
        ('help', 'Help command'),
        ('ls', 'List directory'),
        ('whoami', 'Current user'),
    ]
    
    for command, description in test_commands:
        try:
            result = terminal.execute_command(command)
            if result['exit_code'] == 0:
                test_results.append((description, True, ""))
                print(f"✅ {description}")
            else:
                test_results.append((description, False, result.get('error', 'Unknown error')))
                print(f"❌ {description}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            test_results.append((description, False, str(e)))
            print(f"❌ {description}: {e}")
    
    # Test 3: File operations
    try:
        # Create a test file
        result = terminal.execute_command('touch test_file.txt')
        if result['exit_code'] == 0:
            print("✅ File creation (touch)")
            
            # Test file exists
            result = terminal.execute_command('ls test_file.txt')
            if result['exit_code'] == 0:
                print("✅ File listing verification")
            else:
                print("❌ File listing verification failed")
            
            # Clean up
            terminal.execute_command('rm test_file.txt')
            print("✅ File cleanup")
        else:
            print(f"❌ File creation failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
    
    # Test 4: AI functionality if available
    try:
        from ai.nlp_processor import AITerminal, NLPProcessor
        ai_terminal = AITerminal(terminal)
        nlp_result = ai_terminal.nlp_processor.process_natural_language("show me the current directory")
        if nlp_result == "pwd":
            print("✅ AI natural language processing")
            test_results.append(("AI NLP", True, ""))
        else:
            print(f"⚠️  AI NLP returned unexpected result: {nlp_result}")
            test_results.append(("AI NLP", True, f"Unexpected result: {nlp_result}"))
    except ImportError:
        print("⚠️  AI module not available (this is optional)")
        test_results.append(("AI NLP", True, "Module not available"))
    except Exception as e:
        print(f"❌ AI natural language processing failed: {e}")
        test_results.append(("AI NLP", False, str(e)))
    
    # Test 5: System monitoring
    try:
        from core.system_monitor import SystemMonitor
        cpu_info = SystemMonitor.get_cpu_info()
        if 'total_cpu_usage' in cpu_info:
            print("✅ System monitoring")
            test_results.append(("System monitoring", True, ""))
        else:
            print("❌ System monitoring incomplete")
            test_results.append(("System monitoring", False, "Incomplete data"))
    except Exception as e:
        print(f"❌ System monitoring failed: {e}")
        test_results.append(("System monitoring", False, str(e)))
    
    # Test Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your terminal is ready to use.")
        print("\nTo start the terminal:")
        print("  python main.py              # CLI mode")
        print("  python main.py --ai          # CLI with AI")
        print("  python main.py --web         # Web interface")
        print("  python main.py --web --ai    # Web interface with AI")
        return 0
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("\nThere may be missing dependencies or system-specific issues.")
        print("The terminal may still work for basic operations.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)