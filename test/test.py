import os
from dotenv import load_dotenv
import together
import together
import time
import logging
from typing import Any, Dict, List, Mapping, Optional
from langchain.chains import create_extraction_chain
from langchain.prompts import PromptTemplate
from pydantic import Extra, Field, root_validator
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.utils import get_from_dict_or_env
from langchain.chat_models import ChatOpenAI
from getpass import getpass
from jobportal import Jsearch
from langchain.document_loaders import TextLoader
def load_llm(model_name):
    load_dotenv()
    llm=ChatOpenAI(model=model_name,temperature = 0,
                          openai_api_key =os.environ.get('openai_key') ,         
                          max_tokens=3000                 
                         ) 
    return llm
def val_post_process(val,llm):
    prompt = PromptTemplate(
    input_variables=["skill"],
    template="Summarize  skill: {skill},  in two words seperated by a single space.",
     )
    chain = LLMChain(llm=llm, prompt=prompt)
    lst=[]
    for v in val:
        skill=v["keyword skill"].split()  
        if len(skill)>2:
            v["keyword skill"]=chain.run({'skill':v["keyword skill"]})
        v["keyword skill"]=v["keyword skill"].lower()
      
        lst.append(v["keyword skill"])
    return lst
def extract_keyword(jd,llm):
    schema = {
    "properties": {
        "keyword skill": {"type": "string"},
      
    },
    "required": ["keyword skill"],
   } 
    chain = create_extraction_chain(schema, llm)
    val=chain.run(jd)
    return val
def extract_title(jd,llm):
    prompt = PromptTemplate(
    input_variables=["jd"],
    template="Provide a simple  title for the following  {jd}",
     )
    chain = LLMChain(llm=llm, prompt=prompt) 
    val=chain.run({'jd':jd})
    return val
def extract_result_for_jobs(job_title):
    jsearch = Jsearch()
    jobs= jsearch.fetch_job_description(job_title + "in Canada")
    llm=load_llm('gpt-3.5-turbo')
    results=[]
    for job in jobs:
        try:
            jd="Job description: "+ job['job_description']
            val=extract_keyword(jd,llm)
            result=val_post_process(val,llm)
            job["skills"]=result
            results.append(job)
        except Exception as e:
            job["skills"]=None
            result.append(job)
    return results        
def resume_gen(title,skills,company,link):
    prompt = PromptTemplate(
    input_variables=["title", "skills","data"],
    template="""Information about Ariq:
{data}
You are a resume builder. Build a resume template  for Ariq Rahman in latex based on information about Ariq Rahman and based on the below Job title and keyword skills found in job description. Your Job is to create a resume that is best to tackle the ATS resume system.
Keep the Following into consideration:
1) Keep Contact Education, Work Experience, Personal Project, and Certification section as part of the resume.
2) Select at most 4 relevant Personal Projects under the Project subsection and choose relevant projects .
3) Paraphrase any sentence to densely pack as many keyword skills found in the job description for better chances to pass  the ATS.
4) Bold and highlight the relevant keyword skills and tools, techs  found in Job Description
5) Make the English easy .
6) Start each sentence with Action Verbs found in the Job Description followed by tools used and end with relevant KPIs and highlight the KPIS
7) Make Bullet points for each sentence under a subsection.
Job title:{title}
Keyword skills:{skills}
""",
         )
    llm=load_llm('gpt-3.5-turbo-16k')
    chain = LLMChain(llm=llm, prompt=prompt)
    # loader = TextLoader("test/myself.txt")
    # data=loader.load()
    with open('myself.txt', 'r') as file:
        data = file.read()
    val=chain.run({
    'title': title,
    'skills': skills,
    'data':data
    })
    val+="Link to apply job :{lnk}".format(lnk=link)
    # print(val)
    full_path="Resume_{tit}_{name}.txt".format(tit=title,name=company)
    with open(full_path, 'w') as file:
        file.write(val)
    
    
if __name__ == "__main__":
    result=extract_result_for_jobs("data scientist")
    print(len(result))
    # v=result[0]
    # ks=['coding abstracting', 'coding guidelines', 'coding expertise', 'ehr proficiency', 'paper proficiency', 'communication skills', 'privacy comprehension', 'medical coding', 'assignment methodology', 'coding, abstracting', 'hospital it', 'computer proficiency']
    for v in result:
        resume_gen(v['job_title'],",".join(v["skills"]),v['employer_name'],v['job_apply_link'])
    
    
   