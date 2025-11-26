import requests
import json
import sys

def test_openai_api():
    """Test the OpenAI-compatible API"""
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Check if server is running
    print("1. Testing server status...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Server is running: {response.json()}\n")
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        print("Make sure to run 'python api.py' first!\n")
        return
    
    # Test 2: List models
    print("2. Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{base_url}/v1/models")
        models = response.json()
        print(f"✓ Available models: {json.dumps(models, indent=2)}\n")
    except Exception as e:
        print(f"✗ Error listing models: {e}\n")
    
    # Test 3: Non-streaming chat completion
    print("3. Testing non-streaming chat completion...")
    try:
        payload = {
            "model": "Phi-4-mini-reasoning-qnn-npu:1",
            "messages": [
                {"role": "user", "content": "Quanto é 2+2? Responda apenas o número."}
            ],
            "max_tokens": 100,
            "temperature": 0.1,
            "stream": False
        }
        
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload)
        result = response.json()
        print(f"✓ Response: {json.dumps(result, indent=2)}\n")
    except Exception as e:
        print(f"✗ Error in non-streaming completion: {e}\n")
    
    # Test 4: Streaming chat completion
    print("4. Testing streaming chat completion...")
    try:
        payload = {
            "model": "Phi-4-mini-reasoning-qnn-npu:1",
            "messages": [
                {"role": "user", "content": "Tell me a very short joke."}
            ],
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": True
        }
        
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload, stream=True)
        print("✓ Streaming response:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        print("\n✓ Stream completed\n")
                        break
                    try:
                        data = json.loads(data_str)
                        if data["choices"][0]["delta"].get("content"):
                            print(data["choices"][0]["delta"]["content"], end="", flush=True)
                    except:
                        pass
    except Exception as e:
        print(f"\n✗ Error in streaming completion: {e}\n")

if __name__ == "__main__":
    test_openai_api()
