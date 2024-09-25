# app/main.py

from fastapi import FastAPI, HTTPException
from app.model_manager import download_model, list_downloaded_models, run_sentimental_analysis_model
from app.database import ChatSessionManager
from app.utils import generate_valid_session_id, clear_memory
from app.custom_classes import *
from app.build_graph import graph_app  
from pprint import pprint
import gc 

app = FastAPI()


@app.post("/execute-graph")
async def execute_graph(query: QueryModel):
    try:
        final_output = None
        output = None
        inputs = None
        session_id = generate_valid_session_id(query.video_url)
        inputs = {"question": query.question, "session_id": session_id}
        for output in graph_app.stream(inputs):
            for key, value in output.items():
                pprint(f"Node '{key}':")
                pprint(value, indent=2, width=80, depth=None)
            final_output = value
                
        if final_output and "generation" in final_output:
            chat_manager = ChatSessionManager(session_id)
            chat_manager.add_user_message(query.question)
            chat_manager.add_ai_message(final_output["generation"])
            return {"response": final_output["generation"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate a response.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        clear_memory()
        if final_output and output and inputs:
            del final_output, output, inputs
        gc.collect()

@app.post("/add-session")
async def add_video_session(video: VideoSessionModel):
    try:
        session_id = generate_valid_session_id(video.video_url)
        chat_manager = ChatSessionManager(session_id)
        chat_manager.add_video_session(
            video_title=video.video_title,
            video_url=video.video_url,
            channel_title=video.channel_title,
            description=video.description,
            publish_date=video.publish_date,
            duration=video.duration,
            replace_existing=video.replace_existing
        )
        chat_manager.add_documents_to_db(video.transcript, 
                                        video.comments, 
                                        video.replace_existing)
                
        return {"message": "Session loaded successfully.", "session_id": video.video_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-video-details")
async def get_transcript(videlo_url: str):
    try:
        session_id = generate_valid_session_id(videlo_url)
        chat_manager = ChatSessionManager(session_id)
        video_details = chat_manager.get_video_details()
        return {"details": video_details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-transcript")
async def get_transcript(videlo_url: str):
    try:
        session_id = generate_valid_session_id(videlo_url)
        chat_manager = ChatSessionManager(session_id)
        transcript = chat_manager.get_transcript_from_db()
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-comments")
async def get_comments(videlo_url: str):
    try:
        session_id = generate_valid_session_id(videlo_url)
        chat_manager = ChatSessionManager(session_id)
        comments = chat_manager.get_comments_from_db()
        return {"comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-chat-history")
async def get_chat_history(request: ChatHistoryRequest):
    try:
        session_id = generate_valid_session_id(request.video_url)
        chat_manager = ChatSessionManager(session_id)
        history = chat_manager.get_chat_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/download-model")
async def download_model_endpoint(request: DownloadModelRequest):
    model_name = request.model_name
    model_type = request.model_type
    access_token = request.access_token
    
    try:
        download_message = download_model(model_name, model_type, access_token)
        return {"message": download_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-sentimental-model")
async def run_sentimental(request: RunSentimentalModel):
    result = run_sentimental_analysis_model(request.input_data)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/models")
async def list_models():
    """
    Lista todos los modelos descargados.
    """
    models = list_downloaded_models()
    return {"downloaded_models": models}


