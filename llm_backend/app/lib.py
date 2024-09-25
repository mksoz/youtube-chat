from transformers import (
    AutoModelForCausalLM, AutoModelForSequenceClassification, AutoModelForQuestionAnswering,
    AutoModelForTokenClassification, AutoModelForSeq2SeqLM, AutoModelForMaskedLM,
    AutoModelForImageClassification, AutoModelForAudioClassification, AutoModelForCTC,
    AutoModelForMaskedImageModeling, AutoModelForObjectDetection, AutoModelForSemanticSegmentation,
    AutoModelForSpeechSeq2Seq, AutoModelForVision2Seq, AutoModelWithLMHead, AutoModelForMultipleChoice,
    AutoModelForNextSentencePrediction, AutoModelForPreTraining, AutoModelForDocumentQuestionAnswering,
    AutoModelForVisualQuestionAnswering, AutoModelForZeroShotImageClassification, AutoModel
)

MODEL_CLASS_MAPPING = {
    "causal-lm": AutoModelForCausalLM,
    "sequence-classification": AutoModelForSequenceClassification,
    "question-answering": AutoModelForQuestionAnswering,
    "token-classification": AutoModelForTokenClassification,
    "seq2seq-lm": AutoModelForSeq2SeqLM,
    "masked-lm": AutoModelForMaskedLM,
    "image-classification": AutoModelForImageClassification,
    "audio-classification": AutoModelForAudioClassification,
    "ctc": AutoModelForCTC,  # Connectionist Temporal Classification
    "masked-image-modeling": AutoModelForMaskedImageModeling,
    "object-detection": AutoModelForObjectDetection,
    "semantic-segmentation": AutoModelForSemanticSegmentation,
    "speech-seq2seq": AutoModelForSpeechSeq2Seq,
    "vision2seq": AutoModelForVision2Seq,
    "lm-head": AutoModelWithLMHead,
    "multiple-choice": AutoModelForMultipleChoice,
    "next-sentence-prediction": AutoModelForNextSentencePrediction,
    "pre-training": AutoModelForPreTraining,
    "document-question-answering": AutoModelForDocumentQuestionAnswering,
    "visual-question-answering": AutoModelForVisualQuestionAnswering,
    "zero-shot-image-classification": AutoModelForZeroShotImageClassification,
    "auto-model": AutoModel  # General fallback if model type is unknown or AutoModel should be used
}

MODEL_TYPE_TO_TASK_MAPPING = {
    "causal-lm": "text-generation",
    "sequence-classification": "text-classification",  
    "question-answering": "question-answering",
    "token-classification": "token-classification",  
    "seq2seq-lm": "text2text-generation",
    "masked-lm": "fill-mask",
    "image-classification": "image-classification",
    "audio-classification": "audio-classification",
    "ctc": "automatic-speech-recognition",  
    "masked-image-modeling": "image-segmentation",
    "object-detection": "object-detection",
    "semantic-segmentation": "image-segmentation",
    "speech-seq2seq": "speech-seq2seq", 
    "vision2seq": "vision2seq",  
    "lm-head": "text-generation",
    "multiple-choice": "zero-shot-classification", 
    "next-sentence-prediction": "text-classification",  
    "pre-training": "feature-extraction",  
    "document-question-answering": "document-question-answering",
    "visual-question-answering": "visual-question-answering",
    "zero-shot-image-classification": "zero-shot-image-classification",
    "auto-model": "feature-extraction" 
}
