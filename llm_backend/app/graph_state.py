from typing import List
from typing_extensions import TypedDict
from app.agents import *
from app.tools import retrieve_tool
from app.llm_chain import create_llm
from app.utils import calculate_token_count
from app.database import ChatSessionManager

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """
    session_id: str
    question: str
    generation: str
    documents: List[str]
    
### Nodes

def generate(state: GraphState):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    try:
        print("---GENERATE---")
        generator=None
        question = state["question"]
        documents = state["documents"]
        session_id=state["session_id"]
        chat_manager = ChatSessionManager(session_id)
        history = chat_manager.get_chat_history()
        # RAG generation
        generator=None
        generator = GenerateAnswerAgent()
        calculate_token_count(generator.template, documents, generator.llm.n_ctx)
        generator.set_llm(create_llm(temperature=0.7))
        generation = generator.generate_answer({"history": history, 
                                                "documents": documents, 
                                                "question": question})
        print(f"Answer generated: {generation}")
        return {"documents": documents, "question": question, "generation": generation}
    except Exception as e:
        raise Exception(f"Error: {str(e)}")
    finally:
        if generator is not None:
            del generator 

def grade_documents(state: GraphState):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """
    try:
        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        question = state["question"]
        documents = state["documents"]
        docs_grader=None
        docs_grader=GraderDocsAgent()
        # Score each doc
        filtered_docs = []
        for d in documents:
            score = docs_grader.grade_doc(
                {"document": d.page_content, "question": question}
            )
            if score.lower() == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
        return {"documents": filtered_docs, "question": question}
    except Exception as e:
        raise Exception(f"Error: {str(e)}")
    finally:
        del docs_grader

def transform_query(state: GraphState):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """
    try:
        print("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]
        question_rewriter=None
        question_rewriter = QuestionRewriterAgent()
        # Re-write question
        better_question = question_rewriter.rewrite_question({"question": question})
        return {"documents": documents, "question": better_question}
    
    except Exception as e:
        raise Exception(f"Error: {str(e)}")
    finally:
        del question_rewriter

def search_docs(state: GraphState):
    """
    Route question to web search or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    try:
        retriever=None
        question_router=None
        print("---SEARCH DOCS---")
        question = state["question"]
        session_id = state["session_id"]
        print(question)
        question_router = DocAgent()
        source = question_router.datasource({"question": question})
        target = source.lower()
        print(f"---{target} DATASOURCE TO RAG---")
        tool_input = {"target": target,"session_id": session_id}
        retriever = retrieve_tool.run(tool_input)
        documents = retriever.get_relevant_documents(question)
        return {"documents": documents, "question": question}
    except Exception as e:
        raise Exception(f"Error using retrieve tool: {str(e)}")
    finally:
        del retriever, question_router
    
### Edges ###

def decide_to_generate(state: GraphState):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    try:
        print("---ASSESS GRADED DOCUMENTS---")
        state["question"]
        filtered_documents = state["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
            )
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def grade_generation_v_documents_and_question(state: GraphState):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    try:
        print("---CHECK WELL GROUNDED---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]
        generation_grader=None
        answer_grader=None
        
        generation_grader = DocAnswerAgent()
        score = generation_grader.grade_generation(
            {"documents": documents, "generation": generation}
        )

        if score.lower() == "yes":
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check question-answering
            print("---GRADE GENERATION vs QUESTION---")
            answer_grader = GraderAnswerAgent()
            score = answer_grader.grade_answer({"question": question, "generation": generation})
            
            if score.lower() == "yes":
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"
    except Exception as e:
        raise Exception(f"Error: {str(e)}")
    finally:
        del generation_grader, answer_grader