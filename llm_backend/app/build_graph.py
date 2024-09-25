from langgraph.graph import END, StateGraph, START
from app.graph_state import *

workflow = StateGraph(GraphState)

workflow.add_node("search_docs", search_docs)  
workflow.add_node("generate", generate)  
workflow.add_node("grade_documents", grade_documents) 
workflow.add_node("transform_query", transform_query)  

workflow.add_edge(START, "search_docs")
workflow.add_edge("search_docs", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)

workflow.add_edge("transform_query", "search_docs")

workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",  
        "useful": END, 
        "not useful": "transform_query", 
    },
)

graph_app = workflow.compile()
