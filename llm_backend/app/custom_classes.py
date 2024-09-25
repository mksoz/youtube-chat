from enum import Enum
from pydantic import BaseModel
from typing import Any, Optional, List, Dict, Union

class ModelType(str, Enum):
    causal_lm = "causal-lm"
    sequence_classification = "sequence-classification"
    question_answering = "question-answering"
    token_classification = "token-classification"
    seq2seq_lm = "seq2seq-lm"
    masked_lm = "masked-lm"
    image_classification = "image-classification"
    audio_classification = "audio-classification"
    ctc = "ctc"
    masked_image_modeling = "masked-image-modeling"
    object_detection = "object-detection"
    semantic_segmentation = "semantic-segmentation"
    speech_seq2seq = "speech-seq2seq"
    vision2seq = "vision2seq"
    lm_head = "lm-head"
    multiple_choice = "multiple-choice"
    next_sentence_prediction = "next-sentence-prediction"
    pre_training = "pre-training"
    document_question_answering = "document-question-answering"
    visual_question_answering = "visual-question-answering"
    zero_shot_image_classification = "zero-shot-image-classification"
    auto_model = "auto-model"  # General fallback if model type is unknown or AutoModel should be used
    
class QueryModel(BaseModel):
    video_url: str
    question: str    
 
class VideoSessionModel(BaseModel):
    video_url:str
    video_title:str
    channel_title:str
    description:str
    publish_date:str
    duration:str
    transcript: str
    comments: List[Dict[str, Union[str, int]]]  
    replace_existing: Optional[bool] = False
    
class StartSessionModel(BaseModel):
    video_link: str
    transcript: str
    comments: List[Dict[str, Union[str, int]]] 
    replace_existing: Optional[bool] = False

class AskQuestionModel(BaseModel):
    session_id: str
    question: str

class ChatHistoryRequest(BaseModel):
    video_url: str
    limit: int = 20 
    offset: int = 0 
    
class DownloadModelRequest(BaseModel):
    model_name: str
    model_type: ModelType 
    access_token: Optional[str]
    class Config:
        # Disables the protected namespaces check
        protected_namespaces = ()

class RunSentimentalModel(BaseModel):
    input_data: list[str]