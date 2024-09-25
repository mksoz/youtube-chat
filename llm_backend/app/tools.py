from langchain_core.tools import StructuredTool, ToolException
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from app.database import ChatSessionManager
from app.llm_chain import create_bge_embeddings
from app.utils import config
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["text_splitter"]["chunk_size"],
        chunk_overlap=config["text_splitter"]["chunk_overlap"], 
        separators=config["text_splitter"]["separators"]
    )
    return splitter.split_text(text)

def retrieve_documents(target: str, session_id: str):
    try:
        session_manager = ChatSessionManager(session_id=session_id)
        
        transcript, comments = None, None
        if target == "transcript" or target == "both":
            transcript = session_manager.get_transcript_from_db()
        if target == "comments" or target == "both":
            comments = session_manager.get_comments_from_db()
        
        documents = []
        if transcript:
            for chunk in get_text_chunks(transcript):
                documents.append(Document(page_content=chunk, metadata={"source": "transcript"}))
        
        if comments:
            reformatted_comments = "\n".join(
                f"{comment['author']} ({comment['published_at']}): {comment['text']} [Likes: {comment['like_count']}]"
                for comment in comments)
            for chunk in get_text_chunks(reformatted_comments):
                documents.append(Document(page_content=chunk, metadata={"source": "comments"}))
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            collection_name=f"rag-chroma-{session_id}",
            embedding=create_bge_embeddings(),
        )
        retriever = vectorstore.as_retriever()
        
        return retriever

    except Exception as e:
        raise ToolException(f"Failed to retrieve documents for session {session_id}: {str(e)}")

# Tool creation using StructuredTool.from_function
retrieve_tool = StructuredTool.from_function(
    func=retrieve_documents,
    name="RetrieveDocumentsTool",
    description="Return Chroma vectorestore retriever based on the target (transcript, comments, or both) and the session ID."
)

# Example usage
# relevant_docs = retrieve_tool.run(target="transcript", question="What did the video say about AI?", session_id="123456")
