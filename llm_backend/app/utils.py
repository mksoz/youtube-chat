import os 
import yaml
import hashlib
from transformers import AutoTokenizer
import torch

current_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(current_dir, "config.yaml")

def load_config():
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

def is_model_downloaded(model_name: str) -> bool:
    model_path = os.path.join(config.models_path, model_name)
    return os.path.exists(model_path)

def generate_valid_session_id(video_url):
    video_hash = hashlib.md5(video_url.encode()).hexdigest()
    return f"session_{video_hash}"

def calculate_token_count(prompt: str, chunks: list, n_ctx: int, model_name="mistralai/Mistral-7B-Instruct-v0.3"):
    tokenizer = AutoTokenizer.from_pretrained(model_name, token='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')
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False)
    total_tokens = len(prompt_tokens)

    for chunk in chunks:
        chunk_text=chunk.page_content
        chunk_tokens = tokenizer.encode(chunk_text, add_special_tokens=False)
        total_tokens += len(chunk_tokens)
    
    print(f"Total tokens: {total_tokens}")
    print(f"Model context length (n_ctx): {n_ctx}")
    
    if total_tokens > n_ctx:
        print(f"Warning: The total number of tokens ({total_tokens}) exceeds the model's context window ({n_ctx}).")
    else:
        print(f"The total number of tokens ({total_tokens}) is within the model's context window ({n_ctx}).")

def clear_memory():
    if torch.backends.mps.is_built():
        torch.mps.empty_cache()
        print('Clean mps cache')
    torch.cuda.empty_cache()