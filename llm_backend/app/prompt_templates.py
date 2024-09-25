
datasource_template = """
You are an expert at analyzing content from a video. Your task is to determine the most relevant data source for answering a user's question.\n
Given the question: "{question}", decide which of the following is most appropriate:\n
- "transcript" : if the question is best answered by the video's transcript.\n
- "comments" : if the question is best answered by the user comments.\n
- "both" : if the question requires information from both the transcript and the comments.\n
Provide your answer as a single JSON object with a single key 'target' and one of the three values ("transcript", "comments", or "both"). No additional text or explanations.\n
"""


doc_grader_template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
    Here is the retrieved document: \n\n {document} \n\n
    Here is the user question: {question} \n
    If the document contains keywords related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explanation. Ensure that the JSON is correctly formatted."""

generater_template="""You are an AI assistant specialized in answering questions based on provided information. \n
    Conversation History:
    {history}
    \n ------- \n
    Below are the relevant documents:
    \n ------- \n
    {documents}
    \n ------- \n
    Based on this information, answer the following question clearly and concisely: {question} \n
    Provide your answer with no additional context or explanation."""
 
answer_v_docs_grader_template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
    Here are the facts:
    \n ------- \n
    {documents} 
    \n ------- \n
    Here is the answer: {generation}
    Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. \n
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation. Ensure that the JSON is correctly formatted."""

final_answer_grader_template="""You are a grader assessing whether an answer is useful to resolve a question. \n 
    Here is the answer:
    \n ------- \n
    {generation} 
    \n ------- \n
    Here is the question: {question}
    Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. \n
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation. Ensure that the JSON is correctly formatted."""

rewriter_template="""You are a question re-writer that converts an input question to a better version that is optimized \n 
     for vectorstore retrieval. Look at the initial and formulate an improved question. \n
     Here is the initial question: \n\n {question}. Improved question with no preamble: \n """
     