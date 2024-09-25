from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import chromadb
from app.utils import load_config
import torch

# Load configuration yaml
config=load_config()

def create_llm(model_path=config['llama_cpp_models']['mistral-7b-8q'],
               temperature=0.1, stop=[], grammar_path=None):
    llm = LlamaCpp(
            model_path=model_path,
            n_gpu_layers=config['llama-param']['gpu_layers'],
            n_batch=config['llama-param']['n_batch'],
            max_tokens=256,
            temperature=temperature, 
            n_ctx=2048,
            f16_kv=True,
            verbose=False,
            grammar_path=grammar_path,
            stop=stop
        )
    return llm

def create_bge_embeddings():
    model_name=config["default_embedding_model"]["model_name"]
    
    # Check available devices in order of preference: CUDA (GPU), MPS (Apple Silicon), then CPU
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    embedding = HuggingFaceBgeEmbeddings(
        model_name=model_name, 
        model_kwargs={"device": device}, 
        encode_kwargs={"normalize_embeddings": True},
        # https://huggingface.co/BAAI/bge-m3#faq
        query_instruction = "") 
    return embedding

def create_chat_memory(chat_history):# only keep the last k interactions in memory
    return ConversationBufferWindowMemory(memory_key="history", chat_memory=chat_history, k=3)

def create_prompt_from_template(template):
    return PromptTemplate.from_template(template)

def create_llm_chain(llm, chat_prompt):
    return LLMChain(llm=llm, prompt=chat_prompt)

def load_vectordb(embeddings, collection_name):
    persistent_client = chromadb.PersistentClient(config["chromadb"]["chromadb_path"])

    langchain_chroma = Chroma(
        client=persistent_client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )
    print(f'Vector db instanciado')
    return langchain_chroma

