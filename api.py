from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal
import onnxruntime_genai as og
import uvicorn
import os
import traceback
import json
import time
from contextlib import asynccontextmanager

# Global variables
model = None
tokenizer = None

# Default model path
MODEL_PATH = os.environ.get("MODEL_PATH", r"C:\Users\jluca\.aitk\models\Microsoft\phi-3-mini-128k-instruct-qnn-npu-2\phi-3-mini-128k")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    print(f"Loading model from {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model path does not exist: {MODEL_PATH}")
        yield
        return

    try:
        model = og.Model(MODEL_PATH)
        tokenizer = og.Tokenizer(model)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        traceback.print_exc()
    
    yield
    
    print("Shutting down...")
    # Clean up if necessary
    model = None
    tokenizer = None

app = FastAPI(lifespan=lifespan)

# OpenAI-compatible API models
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "Phi-3-mini-128k-instruct-qnn-npu:1"
    messages: List[Message]
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.1
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False
    repetition_penalty: Optional[float] = 1.05

class GenerateRequest(BaseModel):
    prompt: str
    max_length: int = 2048
    repetition_penalty: float = 1.05
    temperature: float = 0.1
    top_p: float = 0.9

@app.get("/")
def read_root():
    return {"status": "ok", "model_loaded": model is not None}

@app.get("/v1/models")
def list_models():
    """OpenAI-compatible models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": "Phi-3-mini-128k-instruct-qnn-npu:1",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
                "context_length": 4096
            }
        ]
    }

import asyncio

def messages_to_prompt(messages: List[Message]) -> str:
    """Convert OpenAI messages format to Phi-3 chat template"""
    prompt_parts = []
    for msg in messages:
        if msg.role == "system":
            prompt_parts.append(f"<|system|>\n{msg.content}<|end|>")
        elif msg.role == "user":
            prompt_parts.append(f"<|user|>\n{msg.content}<|end|>")
        elif msg.role == "assistant":
            prompt_parts.append(f"<|assistant|>\n{msg.content}<|end|>")
    
    # Add final assistant tag for generation
    prompt_parts.append("<|assistant|>")
    return "\n".join(prompt_parts)

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        prompt = messages_to_prompt(request.messages)
        print(f"Received chat completion request with {len(request.messages)} messages")
        
        input_tokens = tokenizer.encode(prompt)
        input_length = len(input_tokens)
        
        # ONNX QNN model has a fixed max sequence length of 4096 tokens total (input + output)
        # This is due to the positional encoding cache (cos_cache) being fixed at export time
        max_model_length = 4096
        max_output_tokens = request.max_tokens or 2048
        
        # Validate that input + desired output doesn't exceed model capacity
        if input_length + max_output_tokens > max_model_length:
            max_output_tokens = max_model_length - input_length - 10  # Leave small buffer
            if max_output_tokens < 50:
                raise HTTPException(
                    status_code=400,
                    detail=f"Input too long: {input_length} tokens. Maximum total sequence length is {max_model_length} tokens (input + output)."
                )
        
        print(f"Input tokens: {input_length}, Max output tokens: {max_output_tokens}, Total: {input_length + max_output_tokens}")
        
        print("Creating generator params...")
        params = og.GeneratorParams(model)
        print("Setting search options...")
        params.set_search_options(
            max_length=input_length + max_output_tokens,
            repetition_penalty=request.repetition_penalty,
            temperature=request.temperature or 0.1,
            top_p=request.top_p or 0.9,
            do_sample=True
        )
        
        print("Creating generator...")
        generator = og.Generator(model, params)
        print("Appending input tokens...")
        generator.append_tokens(input_tokens)
        print("Generator ready, starting generation...")
        
        if request.stream:
            # Streaming response
            tokenizer_stream = tokenizer.create_stream()
            
            async def stream_generator(gen, stream):
                try:
                    chunk_id = f"chatcmpl-{int(time.time())}"
                    while not gen.is_done():
                        gen.generate_next_token()
                        new_token = gen.get_next_tokens()[0]
                        decoded_token = stream.decode(new_token)
                        
                        chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": decoded_token},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                        await asyncio.sleep(0)
                    
                    # Final chunk
                    final_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    print(f"Error during streaming generation: {e}")
                    traceback.print_exc()
                finally:
                    del gen
                    del stream
            
            return StreamingResponse(stream_generator(generator, tokenizer_stream), media_type="text/event-stream")
        else:
            # Non-streaming response
            tokenizer_stream = tokenizer.create_stream()
            full_text = []
            
            try:
                print("Starting non-streaming generation loop...")
                token_count = 0
                while not generator.is_done():
                    generator.generate_next_token()
                    new_token = generator.get_next_tokens()[0]
                    decoded_token = tokenizer_stream.decode(new_token)
                    full_text.append(decoded_token)
                    token_count += 1
                    if token_count % 10 == 0:
                        print(f"Generated {token_count} tokens...")
                    await asyncio.sleep(0)
                
                print(f"Generation complete. Total tokens generated: {token_count}")
                
                response_text = "".join(full_text)
                print(f"Response length: {len(response_text)} characters")
                
                result = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(input_tokens),
                        "completion_tokens": len(full_text),
                        "total_tokens": len(input_tokens) + len(full_text)
                    }
                }
                print("Sending response...")
                return result
            except Exception as e:
                print(f"Error during non-streaming generation: {e}")
                traceback.print_exc()
                raise
            finally:
                print("Cleaning up generator and tokenizer stream...")
                try:
                    del generator
                    del tokenizer_stream
                except:
                    pass
                print("Cleanup complete.")
                
    except Exception as e:
        print("Error during chat completion:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    """Legacy endpoint for backward compatibility"""
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        print(f"Received prompt: {request.prompt}")
        chat_template = '<|user|>\n{input} <|end|>\n<|assistant|>'
        prompt = chat_template.format(input=request.prompt)
        
        input_tokens = tokenizer.encode(prompt)
        
        params = og.GeneratorParams(model)

        params.set_search_options(
            max_length=request.max_length,
            repetition_penalty=request.repetition_penalty,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=True
        )
        
        generator = og.Generator(model, params)
        generator.append_tokens(input_tokens)
        
        # Create a new stream for this request
        tokenizer_stream = tokenizer.create_stream()
        
        async def token_generator(gen, stream):
            try:
                while not gen.is_done():
                    gen.generate_next_token()
                    new_token = gen.get_next_tokens()[0]
                    decoded_token = stream.decode(new_token)
                    yield decoded_token
                    await asyncio.sleep(0)
            except Exception as e:
                print(f"Error during generation: {e}")
                traceback.print_exc()
            finally:
                # Clean up resources
                del gen
                del stream

        return StreamingResponse(token_generator(generator, tokenizer_stream), media_type="text/plain")
        
    except Exception as e:
        print("Error during generation setup:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
