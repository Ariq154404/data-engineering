import os
from dotenv import load_dotenv
import time
import logging
from langchain.chains import create_extraction_chain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models import ChatOpenAI
from getpass import getpass
from jobportal import Jsearch
from job_types import JobTags
from langchain.document_loaders import TextLoader


def load_llm(model_name):
        load_dotenv()
    #os.environ.get('openai_key') 
        llm=ChatOpenAI(model=model_name,temperature = 0,
                          openai_api_key = os.environ.get('openai_key'),         
                          max_tokens=3000                
                         ) 
        return llm
def resume_filter(title,tag):
    llm=load_llm('gpt-4')
    print(llm)
    with open('myself.txt', 'r') as file:
        data = file.read()
    prompt = PromptTemplate(
    input_variables=["title","data"],
    template="""Information about Ariq:
{data}
Filter out  information for Ariq Rahman  within 500 words that showcases his profile in the {title} role. Filter and list out 5 personal projects that are most relevant to the role of a {title} . Keep information about work experience, contact information, education, certificates in seperate sections. Insert as much as possible keyword skills and words found in  a typical role of {title} person.  Keep the relevant Key performance indicators. Keep subsections for each workplaces.
""",
         )
    chain = LLMChain(llm=llm, prompt=prompt)
    val=chain.run({
    'title': title,
    'data':data
    })
    path='filtered_info/'+tag+'.txt'
    with open(path, 'w') as file:
        file.write(val)

job_tags=JobTags()
jtags=job_tags.get_tags()
for v in jtags:
    print(jtags[v],v)
    resume_filter(jtags[v],v)
