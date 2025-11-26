import requests
import sys

def main():
    url = "http://127.0.0.1:8000/generate"
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Hello, tell me a joke."
    
    payload = {
        "prompt": prompt,
        "max_length": 4096
    }
    
    print(f"Sending request to {url} with prompt: '{prompt}'")
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        print("\nResponse:")
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                print(chunk, end="", flush=True)
        print()
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure 'python api.py' is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
