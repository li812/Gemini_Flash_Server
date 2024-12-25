import sys
import signal
from colorama import Fore, Style
from services.ai_service import generate_content as ai_generate

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n{Fore.YELLOW}Interrupted by user. Exiting...{Style.RESET_ALL}")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage: python test_local.py \"your prompt here\"{Style.RESET_ALL}")
        return 1
    
    try:
        prompt = " ".join(sys.argv[1:])
        print(f"\n{Fore.CYAN}Prompt:{Style.RESET_ALL} {prompt}")
        print(f"{Fore.GREEN}Response:{Style.RESET_ALL}")
        result = ai_generate(prompt)
        print(f"{result}\n")
        return 0

    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
