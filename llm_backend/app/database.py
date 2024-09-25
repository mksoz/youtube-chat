import sqlite3
import os
from langchain_community.chat_message_histories import SQLChatMessageHistory
from app.utils import config
from fastapi import HTTPException

class ChatSessionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.connection_string = config['chat_sessions_database_string']
        self._initialize_db()
        self.message_history = SQLChatMessageHistory(session_id=session_id, connection_string=self.connection_string)

    def _initialize_db(self):
        db_path = config["chat_sessions_database_path"]
        db_dir = os.path.dirname(db_path)
        
        # Crear el directorio si no existe
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables(conn)  
        conn.close()  

    def _create_tables(self, conn):
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT,
                sender_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcript (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT,
                content TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT,
                author TEXT,
                content TEXT,
                published_at DATETIME,
                like_count INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT UNIQUE,
                video_title TEXT,
                video_url TEXT UNIQUE,
                channel_title TEXT,
                description TEXT,
                publish_date TEXT,
                duration TEXT
            )
        """)
        
        conn.commit()

    def table_exists(self, table_name):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        table_exists = cursor.fetchone() is not None
        
        conn.close()
        return table_exists

    def add_video_session(self, video_title, video_url, channel_title, description, publish_date, duration, replace_existing=False):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM video_details WHERE video_url = ?", (video_url,))
        existing_video = cursor.fetchone()

        if existing_video:
            if replace_existing:
                cursor.execute("""
                    UPDATE video_details 
                    SET video_title = ?, channel_title = ?, description = ?, publish_date = ?, duration = ? 
                    WHERE video_url = ?
                """, (video_title, channel_title, description, publish_date, duration, video_url))
                print(f"Existing video updated for session {self.session_id}.")
            else:
                conn.close()
                return None

        else:
            cursor.execute("""
                INSERT INTO video_details (session_key, video_title, video_url, channel_title, description, publish_date, duration) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (self.session_id, video_title, video_url, channel_title, description, publish_date, duration)
            )
            print(f"New video session created for session {self.session_id}.")

        conn.commit()
        conn.close()

    def add_documents_to_db(self, transcript=None, comments=[], replace_existing=False):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM transcript WHERE session_key = ?", (self.session_id,))
        existing_transcript = cursor.fetchone()
        
        cursor.execute("SELECT * FROM comments WHERE session_key = ?", (self.session_id,))
        existing_comments = cursor.fetchone()

        if existing_transcript or existing_comments:
            if not replace_existing:
                print(f"Documents already exist for session {self.session_id} and replace_existing is False. No changes made.")
                conn.close()
                return None

        if replace_existing:
            cursor.execute("DELETE FROM transcript WHERE session_key = ?", (self.session_id,))
            cursor.execute("DELETE FROM comments WHERE session_key = ?", (self.session_id,))
            conn.commit()
            print(f"Existing documents deleted for session {self.session_id}. Replacing with new documents.")

        if transcript:
            cursor.execute("INSERT INTO transcript (session_key, content) VALUES (?, ?)", (self.session_id, transcript))

        for comment in comments:
            cursor.execute(
                "INSERT INTO comments (session_key, author, content, published_at, like_count) VALUES (?, ?, ?, ?, ?)",
                (self.session_id, comment['author'], comment['text'], comment['published_at'], comment['like_count'])
            )

        conn.commit()
        conn.close()
        print(f"Transcript and comments added to db for session {self.session_id}.")
      
    def add_user_message(self, message):
        self.message_history.add_user_message(message)

    def add_ai_message(self, message):
        self.message_history.add_ai_message(message)

    def get_video_details(self):
        try:
            conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_details';")
            table_exists = cursor.fetchone()

            if not table_exists:
                return ""

            cursor.execute("SELECT video_title, channel_title, description, publish_date, duration FROM video_details WHERE session_key = ?", (self.session_id,))
            video_details = cursor.fetchone()

            if not video_details:
                return ""
            conn.close()

            return {
                "video_title": video_details[0],
                "channel_title": video_details[1],
                "description": video_details[2],
                "publish_date": video_details[3],
                "duration": video_details[4],
            }

        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Error con la base de datos: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_chat_history(self):
        return self.message_history.messages

    def get_transcript_from_db(self):
        try:
            conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM transcript WHERE session_key = ?", (self.session_id,))
            transcript = cursor.fetchone()
            conn.close()
            print(transcript)
            if transcript:
                return transcript[0]
            else:
                return "No transcript to show"
            
        except Exception as e:
            raise ValueError(f"Error getting trancript: {str(e)}.")
        
    def get_comments_from_db(self):
        try:
            conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT author, content, published_at, like_count FROM comments WHERE session_key = ?", (self.session_id,))
            comments = cursor.fetchall()
            conn.close()
            print(comments)
            if comments:
                return [{"author": row[0], "text": row[1], "published_at": row[2], "like_count": row[3]} for row in comments]
            else:
                return "No comments to show"
        except Exception as e:
            raise ValueError(f"Error getting comments: {str(e)}.")
        
    def save_message_to_db(self, sender_type, content):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (session_key, sender_type, content) VALUES (?, ?, ?)",
                       (self.session_id, sender_type, content))
        conn.commit()
        conn.close()

    def load_messages_from_db(self):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT sender_type, content FROM chat_history WHERE session_key = ? ORDER BY id", (self.session_id,))
        messages = cursor.fetchall()
        conn.close()
        return messages
    
    def delete_video_session(self):
        conn = sqlite3.connect(config['chat_sessions_database_path'], check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chat_history WHERE session_key = ?", (self.session_id,))
        cursor.execute("DELETE FROM transcript WHERE session_key = ?", (self.session_id),)
        cursor.execute("DELETE FROM comments WHERE session_key = ?", (self.session_id),)
        cursor.execute("DELETE FROM video_details WHERE session_key = ?", (self.session_id),)
        conn.commit()
        conn.close()
        

