import sys
import requests
from colorama import Fore, Style

def main():
    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage: python test_server.py \"your prompt here\"{Style.RESET_ALL}")
        return 1
    
    prompt = " ".join(sys.argv[1:])
    print(f"\n{Fore.CYAN}Prompt:{Style.RESET_ALL} {prompt}")
    print(f"{Fore.GREEN}Response:{Style.RESET_ALL}")

    try:
        response = requests.post('http://localhost:5050/api/llm/generate', json={'prompt': prompt})
        response.raise_for_status()
        result = response.json().get('response', 'No response')
        print(f"{result}\n")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
