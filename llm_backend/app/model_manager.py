# app/model_manager.py
from transformers import pipeline, AutoModel, AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional, Dict, Any
import os
from app.utils import load_config
from app.lib import MODEL_CLASS_MAPPING, MODEL_TYPE_TO_TASK_MAPPING
import torch

config=load_config()
MODEL_DIR = config["model_path"]
DEFAULT_SENTIMENTAL_MODEL = config["default_model_sentiment"]

os.makedirs(MODEL_DIR, exist_ok=True)

def get_task_from_model_type(model_type: str) -> str:
    """
    Get pipeline task

    Args:
        model_type (str): model type

    Returns:
        str: pipeline task
    """
    task = MODEL_TYPE_TO_TASK_MAPPING.get(model_type)
    if task:
        return task
    else:
        raise ValueError(f"task not suppotered for model '{model_type}'.")

def is_model_downloaded(model_name: str) -> bool:
    sanitized_model_name = model_name.replace('/', '_')
    model_path = os.path.join(MODEL_DIR, sanitized_model_name)
    
    return os.path.isdir(model_path)

def download_model(model_name: str, model_type: str = None, token: str = None) -> str:
    
    if is_model_downloaded(model_name):
        return f"Model '{model_name}' already downloaded."

    sanitized_model_name = model_name.replace('/', '_')
    model_path = os.path.join(MODEL_DIR, sanitized_model_name)
    
    # Intentar cargar el modelo usando el tipo especificado
    if model_type:
        model_class = MODEL_CLASS_MAPPING.get(model_type)
        if model_class:
            try:
                model = model_class.from_pretrained(model_name, token=token)
                tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
                model.save_pretrained(model_path, token=token)
                tokenizer.save_pretrained(model_path, token=token)
                with open(os.path.join(model_path, 'model_type.txt'), 'w') as f:
                    f.write(model_type)
                    
                return f"Model and tokennizer '{model_name}' downloaded and stored '{model_path}' using type '{model_type}'."
            except Exception as e:
                print(f"Error al cargar con el tipo '{model_type}': {e}")
    
    for model_class in MODEL_CLASS_MAPPING.values():
        try:
            model = model_class.from_pretrained(model_name, token=token)
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
            model.save_pretrained(model_path, token=token)
            tokenizer.save_pretrained(model_path, token=token)
            with open(os.path.join(model_path, 'model_type.txt'), 'w') as f:
                f.write(model_type)
                
            return f"Model and tokennizer '{model_name}' downloaded and stored in '{model_path}' using class '{model_class.__name__}'."
        except Exception as e:
            if model_class == AutoModel:
                raise RuntimeError(f"Cannot be loaded '{model_name}'. Error: {e}")
            continue  # Continuar con la siguiente clase si falla

def get_model_class_from_type(model_type: str):
    return MODEL_CLASS_MAPPING.get(model_type, AutoModel)

def list_downloaded_models() -> Dict[str, str]:
    models = {}
    for model_name in os.listdir(MODEL_DIR):
        model_path = os.path.join(MODEL_DIR, model_name)
        if os.path.isdir(model_path):
            models[model_name] = model_path
    return models

def run_sentimental_analysis_model(phrases: list[str]) -> Optional[Dict[str, Any]]:
    
    if not is_model_downloaded(DEFAULT_SENTIMENTAL_MODEL):
        try:
            download_model(DEFAULT_SENTIMENTAL_MODEL,"sequence-classification")
        except Exception as e:
            return e
    
    model_name=DEFAULT_SENTIMENTAL_MODEL
    sanitized_model_name = model_name.replace('/', '_')
    model_path = os.path.join(MODEL_DIR, sanitized_model_name)
    
    try:
        llm = AutoModelForSequenceClassification.from_pretrained(model_path)
    except Exception as e:
        return {"error": f"Error loading model '{model_name}': {e}"}

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    except Exception as e:
        return {"error": f"Error loading tokennizer '{model_name}': {e}"}
    
    # Check for available device in the order: CUDA (GPU) -> MPS (Apple Silicon) -> CPU
    if torch.cuda.is_available():
        device_index = 0  # Using the first available GPU
    elif torch.backends.mps.is_available():
        device_index = 0  # MPS does not require an index, but this is for compatibility with the pipeline's device argument
    else:
        device_index = -1  # CPU is represented with -1 in the pipeline's device argument

    # Initialize the pipeline
    pipe = pipeline(
        task="text-classification",
        model=llm,
        tokenizer=tokenizer,
        return_all_scores=True,
        device=device_index,  # GPU/MPS if available, otherwise CPU
        max_length=512,
        truncation=True
    )
    total_scores = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}

    for phrase in phrases:
        results = pipe(phrase)
        for result in results:
            for label_score in result:
                total_scores[label_score['label'].lower()] += label_score['score']

    num_phrases = len(phrases)
    avg_scores = {label: score / num_phrases for label, score in total_scores.items()}

    return avg_scores
