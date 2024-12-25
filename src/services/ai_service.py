import os
from pathlib import Path
import google.generativeai as genai
from services.encryption_util import decrypt_message

def load_api_key(api_key_path="api.txt", key_path="key.txt"):
    try:
        with open(api_key_path, 'r') as file:
            encrypted_api_key = file.read().strip()
        with open(key_path, 'r') as file:
            key = file.read().strip()
        return decrypt_message(encrypted_api_key, key)
    except FileNotFoundError:
        raise FileNotFoundError("API key file not found")

def configure_genai():
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    model_name = Path("src/model.txt").read_text().strip()
    return genai.GenerativeModel(model_name)

def generate_content(prompt: str) -> str:
    try:
        model = configure_genai()
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating content: {str(e)}"

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"
    print(generate_content(test_prompt))