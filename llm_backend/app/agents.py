from langchain.prompts import PromptTemplate
from app.llm_chain import create_llm
from app.prompt_templates import *
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import json
from app.utils import config

class BaseAgent:
    def __init__(self, template, input_variables, parser):
        self.llm = create_llm() 
        self.parser = parser
        self.template= template
        self.prompt = PromptTemplate(template=template, input_variables=input_variables)
        self.llm_chain = self.prompt | self.llm | self.parser
        
    def run_chain(self, inputs):
        return self.llm_chain.invoke(inputs)

    def set_llm(self, llm):
        self.llm = llm
        self.llm_chain = self.prompt | self.llm | self.parser

class DocAgent(BaseAgent):
    def __init__(self, template=datasource_template, 
                 input_variables=["question"], 
                 parser=StrOutputParser()):
        super().__init__(template, input_variables, parser)
        self.set_llm(create_llm(grammar_path=config['grammar']['target_path']))  
              
    def datasource(self, input):
        response = self.run_chain(input)
        if isinstance(response, str):
            try:
                json_response = json.loads(response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        else:
            json_response = response

        if "target" not in json_response:
            raise ValueError("Invalid JSON format: Missing 'score' key.")

        return json_response["target"]

class GraderDocsAgent(BaseAgent):
    def __init__(self, template=doc_grader_template, 
                 input_variables=["question", "documents"], 
                 parser=JsonOutputParser()):
        super().__init__(template, input_variables, parser)
        self.set_llm(create_llm(grammar_path=config['grammar']['score_path']))  
        
    def grade_doc(self, input):
        response = self.run_chain(input)
        if isinstance(response, str):
            try:
                json_response = json.loads(response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        else:
            json_response = response

        if "score" not in json_response:
            raise ValueError("Invalid JSON format: Missing 'score' key.")

        return json_response["score"]

class GenerateAnswerAgent(BaseAgent):
    def __init__(self, template=generater_template, 
                 input_variables=["question", "documents"], 
                 parser=StrOutputParser()):
        super().__init__(template, input_variables, parser)
    
    def generate_answer(self, input):
        response = self.run_chain(input)
        return response

class DocAnswerAgent(BaseAgent):
    def __init__(self, template=answer_v_docs_grader_template, 
                 input_variables=["documents", "generation"], 
                 parser=StrOutputParser()):
        super().__init__(template, input_variables, parser)
        self.set_llm(create_llm(grammar_path=config['grammar']['score_path']))  

    def grade_generation(self, input):
        response = self.run_chain(input)
        if isinstance(response, str):
            try:
                json_response = json.loads(response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        else:
            json_response = response

        if "score" not in json_response:
            raise ValueError("Invalid JSON format: Missing 'score' key.")

        return json_response["score"]

class GraderAnswerAgent(BaseAgent):
    def __init__(self, template=final_answer_grader_template, 
                 input_variables=["generation", "question"], 
                 parser=StrOutputParser()):
        super().__init__(template, input_variables, parser)
        self.set_llm(create_llm(grammar_path=config['grammar']['score_path']))  
        
    def grade_answer(self, input):
        response = self.run_chain(input)
        if isinstance(response, str):
            try:
                json_response = json.loads(response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        else:
            json_response = response

        if "score" not in json_response:
            raise ValueError("Invalid JSON format: Missing 'score' key.")

        return json_response["score"]

class QuestionRewriterAgent(BaseAgent):
    def __init__(self, template=rewriter_template, 
                 input_variables=["question"], 
                 parser=StrOutputParser()):
        super().__init__(template, input_variables, parser)
    
    def rewrite_question(self, input):
        response = self.run_chain(input)
        return response