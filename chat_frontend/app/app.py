import streamlit as st
from googleapiclient.errors import HttpError
from handlers import YouTubeHandler
from utils import load_config, plot_sentiment_pie, get_avatar
import requests
from html_templates import css

config = load_config()

MODEL_DIR = config["model_path"]
DOWNLOAD_ENDPOINT = config["download_model_endpoint"]
LIST_MODELS_ENDPOINT = config["list_models_endpoint"]
SENTIMENTAL_MODEL_ENDPOINT = config["run_sentimental_model_endpoint"]

# Configuración de la página
st.set_page_config(page_title="Chat to YouTube", page_icon=config['yt_icon'],layout="wide")

# Barra lateral - Configuración
def render_sidebar():
    st.sidebar.title("Settings")

    # API Key Input y botón de validación
    api_key_col1, api_key_col2 = st.sidebar.columns([3, 1])
    with api_key_col1:
        api_key = st.text_input("YouTube API Key", type="password", value=config['youtube_api_key'])
        if api_key:
            st.session_state.api_key = api_key  # Guardar en session_state
    with api_key_col2:
        validate_api_key_button = st.button("Validate key")
    
    # Video URL Input
    video_url_col1, video_url_col2 = st.sidebar.columns([3, 1])
    with video_url_col1:
        video_url = st.text_input("YouTube Video Link")
        if video_url:
            st.session_state.video_url = video_url  # Guardar en session_state
    with video_url_col2:
        if video_url:
            validate_video_url_button = st.button("Validate URL")
        else:
            validate_video_url_button = None
    
    # Inicializar botones adicionales
    chat_video_button = None 
    set_transcript_button = None
    set_comments_button = None
    analyze_sentiment_button = None

    youtube_handler = None
    if "api_key" in st.session_state:
        youtube_handler = YouTubeHandler(st.session_state.api_key)
        st.session_state.youtube_handler = youtube_handler
    
    # Inicializar botones adicionales y colocarlos en una fila
    if video_url:
        col1, col2, col3 = st.sidebar.columns([2, 2, 2])  # Agrandar el botón de Chat
        with col1:
            set_comments_button = st.button("Comments")
        with col2:
            set_transcript_button = st.button("Transcript")
        with col3:
            chat_video_button = st.button("Chat", key="chat_button")
        video_title,channel_title,description,publish_date, duration = get_video_details(st.session_state.youtube_handler,
                                                                                        st.session_state.video_url)
        st.sidebar.write(f"** Title: {video_title} **")
        st.sidebar.write(f"** Channel: {channel_title} **")
        st.sidebar.write(f"{description}")
        st.sidebar.write(f"Published on {publish_date}")
        analyze_sentiment_button = st.sidebar.button("Analyse Sentiment of Comments")
    else:
        st.sidebar.write("Enter the link to the video to enable processing")

    # Validar la API Key
    if validate_api_key_button:
        validate_api_key(youtube_handler, st.session_state.api_key)

    # Validar la URL del Video
    if validate_video_url_button:
        validate_video_url(youtube_handler, st.session_state.video_url)

    # Procesar el video al hacer clic en el botón "Chat"
    if chat_video_button:
        if "youtube_handler" in st.session_state and "video_url" in st.session_state:
            add_session(st.session_state.youtube_handler, st.session_state.video_url)
        else:
            st.error("No API Key or video link has been configured")

    # Obtener transcripción
    if set_transcript_button:
        show_transcript(st.session_state.video_url)

    # Obtener comentarios
    if set_comments_button:
        show_comments(st.session_state.video_url)

    # Analizar sentimiento de los comentarios
    if analyze_sentiment_button:
        analyze_sentiment(st.session_state.youtube_handler, st.session_state.video_url)

# Área principal - Chat
def render_chat():
    st.title("YouTube Chat")
    st.write(css, unsafe_allow_html=True)

    # Verificar que los datos requeridos estén en session_state
    if "session_key" not in st.session_state:
        st.warning("Please process the video in the sidebar before continuing")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Cargar historial de chat si es la primera vez
    if not st.session_state.messages:
        load_chat_history()

    # Mostrar mensajes cargados
    for sender_type, content in st.session_state.messages:
        with st.chat_message(name=sender_type, avatar=get_avatar(sender_type)):
            st.write(content)

    # Input del usuario
    user_input = st.chat_input("Type your message here", key="user_input")

    if user_input:
        with st.chat_message(name="human", avatar=get_avatar("human")):
            st.write(user_input)
        
        with st.spinner('Esperando respuesta...'):
            llm_response = send_question(user_input)
        with st.chat_message(name="ai", avatar=get_avatar("ai")):
            st.write(llm_response)
        
        st.session_state.messages.append(("human", user_input))
        st.session_state.messages.append(("ai", llm_response))
 
def get_video_details(youtube_handler, video_url):
    try:
        response = requests.get(f"{config['backend_url']}/get-video-details", params={"videlo_url": video_url})
        if response.status_code == 200:
            details = response.json().get("details")
            if details:
                video_title = details.get('video_title')
                channel_title = details.get('channel_title')
                description = details.get('description')
                publish_date = details.get('publish_date')
                duration = details.get('duration')
            else:
                video_id = youtube_handler.extract_video_id(video_url)
                video_details = youtube_handler.extract_video_details(youtube_handler.get_video_details(video_id))
                video_title = video_details['title']
                channel_title = video_details['channel_title']
                description = video_details['description']
                publish_date = video_details['published_at']
                duration = video_details['duration']
            return video_title, channel_title, description, publish_date, duration
        else:
            return "", "", "", "", ""
    except Exception as e:
        st.sidebar.error(f"An error occurred in obtaining details of the video: {str(e)}")
        return "", "", "", "", ""    
             
def add_session(youtube_handler, video_url):
    try:
        transcript = get_transcript(youtube_handler, video_url)
        comments = get_comments(youtube_handler, video_url)
        video_id = youtube_handler.extract_video_id(video_url)
        video_details = youtube_handler.get_video_details(video_id)
        video_info = youtube_handler.extract_video_details(video_details)
        json={
                "video_url": video_url,
                "video_title":video_info.get('title',''),
                "channel_title":video_info.get('channel_title',''),
                "description":video_info.get('description',''),
                "publish_date":video_info.get('published_at',''),
                "duration":str(video_info.get('duration','')),
                "transcript": transcript,
                "comments": comments,
                "replace_existing":False
            }
        response = requests.post(f"{config['backend_url']}/add-session", json=json)
        if response.status_code == 200:
            st.session_state.session_key = response.json().get("session_id")
            st.success("Session successfully logged in and data added.")
            # Recargar el historial del chat
            load_chat_history()
        else:
            st.error(f"Error logging in: {response.text}")
    except Exception as e:
        st.sidebar.error(f"An error occurred adding session: {str(e)}")

def validate_api_key(youtube_handler, api_key):
    if not api_key:
        st.sidebar.warning("No API key has been entered. Enter an API key to use YouTube features.")
    else:
        try:
            test_video_id = "Ks-_Mh1QhMc"
            request = youtube_handler.youtube.videos().list(part="snippet", id=test_video_id)
            response = request.execute()
            st.sidebar.success("Valid API key.")
        except HttpError as e:
            if e.resp.status in [400, 403, 401]:
                st.sidebar.error("Invalid or expired API key")
            else:
                st.sidebar.error(f"An error occurred with the YouTube API:  {str(e)}")
        except Exception as e:
            st.sidebar.error(f"An unexpected error occurred: {str(e)}")

def validate_video_url(youtube_handler, video_url):
    if not video_url:
        st.sidebar.warning("No video link has been entered. Please enter a video link to continue.")
    else:
        video_id = youtube_handler.extract_video_id(video_url)
        try:
            if youtube_handler and youtube_handler.check_video_exists(video_id):
                st.sidebar.success("The video exists!")
                return True
            else:
                st.sidebar.error("The video does not exist or the URL cannot be processed.")
                return False
        except Exception as e:
            st.sidebar.error(f"An error occurred with the video verification: {str(e)}")
            return False
        
def show_transcript(video_url):
    with st.spinner('Loading the transcript...'):
        response = requests.get(f"{config['backend_url']}/get-transcript", params={"videlo_url": video_url})
        if response.status_code == 200:
            transcript = response.json().get("transcript")
            st.write("### Video transcript")
            st.write(transcript)
        else:
            st.error(f"Error loading transcript: {response.text}")

def show_comments(video_url):
    with st.spinner('Loading comments...'):
        response = requests.get(f"{config['backend_url']}/get-comments", params={"videlo_url": video_url})
        if response.status_code == 200:
            comments = response.json().get("comments")
            st.write("### Video comments")
            if comments == "No comments to show":
                st.markdown(comments)
            else:
                for comment in comments:
                    st.markdown(f"**{comment['author']}**: {comment['text']} ({comment['published_at']}) [Likes: {comment['like_count']}]")
        else:
            st.error(f"Error loading comments: {response.text}")

def get_transcript(youtube_handler, video_url):
    try:
        video_id = youtube_handler.extract_video_id(video_url)
        transcript = youtube_handler.get_transcript(video_id)
        full_text_transcript = youtube_handler.get_full_transcript_text(transcript)
        return full_text_transcript
    except Exception as e:
        st.error(f"Error getting the transcript: {str(e)}")
        return ""

def get_comments(youtube_handler, video_url):
    try:
        video_id = youtube_handler.extract_video_id(video_url)
        comments = youtube_handler.get_youtube_comments(video_id)
        comment_details = youtube_handler.extract_comment_details(comments)
        formatted_comments = []
        for comment in comment_details:
            formatted_comments.append({
                "author": comment['author'],
                "text": comment['text'],
                "published_at": comment['published_at'],
                "like_count": comment['like_count']
            })
        return formatted_comments
    except Exception as e:
        st.error(f"Error getting comments: {str(e)}")
        return []

def analyze_sentiment(youtube_handler, video_url):
    with st.spinner('Analysing the sentiment of the comments....'):
        try:
            video_id = youtube_handler.extract_video_id(video_url)
            comments = youtube_handler.get_youtube_comments(video_id)
            comment_details = youtube_handler.extract_comment_details(comments)
            texts = [comment['text'] for comment in comment_details]

            video_details = youtube_handler.get_video_details(video_id)
            video_info = youtube_handler.extract_video_details(video_details)
            like_count = int(video_info['like_count'] or 0)
            dislike_count = int(video_info['dislike_count'] or 0)
            comment_count = int(video_info['comment_count'] or 0)
            st.sidebar.write(f"** {like_count} likes vs {dislike_count} dislikes ** ")
            st.sidebar.write(f"**Comment number:** {comment_count}")

            input_data = {"input_data": texts}
            run_response = requests.post(f"{config['backend_url']}/run-sentimental-model", json=input_data)
            if run_response.status_code == 200:
                sentiment_scores = run_response.json()
                fig2 = plot_sentiment_pie(sentiment_scores)
                st.sidebar.pyplot(fig2, transparent=True)
            else:
                st.write("Error running the model: ", run_response.text)
        except Exception as e:
            st.error(f"A mistake was made in analysing the sentiment: {str(e)}")
        
def load_chat_history():
    response = requests.post(f"{config['backend_url']}/get-chat-history", json={
        "video_url": st.session_state.video_url,
        "limit": 20,
        "offset": 0
    })
    if response.status_code == 200:
        history = response.json().get("history", [])
        st.session_state.messages = [
            (message['type'], message['content']) for message in history
        ]
    else:
        st.error(f"Error al cargar el historial del chat: {response.text}")

def send_question(user_input):
    response = requests.post(f"{config['backend_url']}/execute-graph", json={
        "video_url": st.session_state.video_url,
        "question": user_input
    })
    if response.status_code == 200:
        return response.json().get("response")
    return f"Error {response.status_code}: {response.text}"

# Renderizar la aplicación completa
def main():
    render_sidebar()
    render_chat()

if __name__ == "__main__":
    main()
