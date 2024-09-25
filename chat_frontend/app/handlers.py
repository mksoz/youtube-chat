import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from datetime import timedelta

class YouTubeHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_youtube_comments(self, video_id):
        comments = []
        next_page_token = None

        while True:
            request = self.youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                textFormat='plainText',
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()
            comments.extend(response['items'])

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return comments

    def extract_comment_details(self, comments):
        all_comments = []
        for comment_thread in comments:
            top_comment = comment_thread['snippet']['topLevelComment']['snippet']
            comment_details = {
                'author': top_comment.get('authorDisplayName'),
                'author_profile_image': top_comment.get('authorProfileImageUrl'),
                'author_channel_url': top_comment.get('authorChannelUrl'),
                'text': top_comment.get('textDisplay'),
                'published_at': top_comment.get('publishedAt'),
                'updated_at': top_comment.get('updatedAt'),
                'like_count': top_comment.get('likeCount'),
                'reply_count': comment_thread['snippet'].get('totalReplyCount', 0),
                'replies': []
            }

            if 'replies' in comment_thread:
                for reply in comment_thread['replies']['comments']:
                    reply_snippet = reply['snippet']
                    reply_details = {
                        'author': reply_snippet.get('authorDisplayName'),
                        'author_profile_image': reply_snippet.get('authorProfileImageUrl'),
                        'author_channel_url': reply_snippet.get('authorChannelUrl'),
                        'text': reply_snippet.get('textDisplay'),
                        'published_at': reply_snippet.get('publishedAt'),
                        'updated_at': reply_snippet.get('updatedAt'),
                        'like_count': reply_snippet.get('likeCount'),
                    }
                    comment_details['replies'].append(reply_details)
                    
            all_comments.append(comment_details)
            
        return all_comments
    
    def format_comments_for_display(self, comments):
        """
        Formatea una lista de detalles de comentarios para su visualización en Streamlit.
        
        Args:
            comments (list): Lista de diccionarios con detalles de los comentarios.
        
        Returns:
            list: Lista de strings formateados para mostrar en Streamlit.
        """
        formatted_comments = []
        for comment in comments:
            # Formatear el comentario con la imagen de perfil, nombre y texto
            formatted_comment = f"![{comment['author']} profile image]({comment['author_profile_image']}) **{comment['author']}**: {comment['text']}"
            formatted_comments.append(formatted_comment)
            
            # Formatear las respuestas, si existen
            for reply in comment['replies']:
                formatted_reply = f"↳ ![{reply['author']} profile image]({reply['author_profile_image']}) **{reply['author']}**: {reply['text']}"
                formatted_comments.append(formatted_reply)
                
        return formatted_comments
    
    def get_transcript(self, video_id):
        try:
            # Listar todas las transcripciones disponibles
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Buscar la transcripción que fue "manualmente creada" o es la primera en la lista (que normalmente es el idioma original)
            for transcript in transcript_list:
                if transcript.is_generated:
                    continue  # Ignorar transcripciones generadas automáticamente
                else:
                    # Obtener la transcripción manualmente creada
                    return transcript.fetch()

            # Si no hay transcripción manualmente creada, usar la primera disponible (probablemente generada)
            return transcript_list.find_transcript([transcript.language_code for transcript in transcript_list]).fetch()

        except NoTranscriptFound:
            return f"No se pudo obtener la transcripción para el video. No se encontraron transcripciones disponibles."
        except TranscriptsDisabled:
            return f"Las transcripciones están deshabilitadas para el video."
        except VideoUnavailable:
            return f"El video no está disponible."
        except Exception as e:
            return f"Ocurrió un error inesperado: {str(e)}"
    
    def get_full_transcript_text(self, transcript):
        """
        Recibe la transcripción en formato de lista de diccionarios y devuelve un único string con todo el texto.
        """
        full_text = ' '.join([item['text'] for item in transcript])
        return full_text
    
    @staticmethod
    def extract_video_id(url):
        video_id = re.search(r'(?<=v=)[^&#]+', url)
        if not video_id:
            video_id = re.search(r'(?<=be/)[^&#]+', url)
        if video_id:
            return video_id.group(0)
        else:
            raise ValueError("No se pudo extraer la ID del video de la URL proporcionada.")
    
    @staticmethod
    def extract_video_id(url):
        video_id = re.search(r'(?<=v=)[^&#]+', url)
        if not video_id:
            video_id = re.search(r'(?<=be/)[^&#]+', url)
        if video_id:
            return video_id.group(0)
        else:
            raise ValueError("No se pudo extraer la ID del video de la URL proporcionada.")

    def get_video_details(self, video_id):
        request = self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        return response['items'][0]

    def extract_video_details(self, video_details):
        snippet = video_details.get('snippet', {})
        statistics = video_details.get('statistics', {})
        content_details = video_details.get('contentDetails', {})

        duration = self.convert_duration_to_seconds(content_details.get('duration'))

        # Asegurarse de que estos valores sean enteros y manejar posibles None
        view_count = int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0
        like_count = int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0
        dislike_count = int(statistics.get('dislikeCount', 0)) if statistics.get('dislikeCount') else 0
        comment_count = int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else 0

        video_info = {
            'title': snippet.get('title', 'N/A'),
            'description': snippet.get('description', 'N/A'),
            'tags': snippet.get('tags', []),
            'published_at': snippet.get('publishedAt', 'N/A'),
            'channel_title': snippet.get('channelTitle', 'N/A'),
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'duration': duration,
            'category_id': snippet.get('categoryId', 'N/A')
        }
        
        return video_info


    @staticmethod
    def convert_duration_to_seconds(duration):
        if duration:
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            if not match:
                return None
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
        return None
    
    def check_video_exists(self, video_id):
        """
        Verifica si un video de YouTube existe usando la API de YouTube.
        
        Args:
            video_id (str): El ID del video de YouTube.

        Returns:
            bool: True si el video existe, False si no.
        """
        try:
            request = self.youtube.videos().list(
                part="id",
                id=video_id
            )
            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                return True
            else:
                return False

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return False