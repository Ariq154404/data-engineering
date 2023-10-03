
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
from langchain.document_loaders import TextLoader
from database import CassandraSessions
from airflow import DAG
from datetime import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.decorators import dag, task

def resume_gen(title,skills,company,link,job_tag,cnt):
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
    llm=load_llm('gpt-4')
    chain = LLMChain(llm=llm, prompt=prompt)
    # loader = TextLoader("test/myself.txt")
    # data=loader.load()
    # with open('/opt/airflow/dags/myself.txt', 'r') as file:
    #     data = file.read()
    path='/opt/airflow/dags/filtered_info/'+job_tag+'.txt'
    with open(path, 'r') as file:
        data = file.read()
    val=chain.run({
    'title': title,
    'skills': skills,
    'data':data
    })
    
    val+="Link to apply job :{lnk}".format(lnk=link)
    # print(val)
    full_path="/opt/airflow/dags/resumes/Resume_{name}_{count}.txt".format(name=company,count=cnt)

    print("FULL_PATH")
    print(full_path)
    with open(full_path, 'w') as file:
        file.write(val)
def load_llm(model_name):
        load_dotenv()
    #os.environ.get('openai_key') 
        llm=ChatOpenAI(model=model_name,temperature = 0,
                          openai_api_key = os.environ.get('openai_key') ,         
                          max_tokens=2000                
                         ) 
        return llm
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}
@dag(
    dag_id='resume_generation_dag',
    default_args=default_args,
    description='a dag to generate resume from keyword',
    schedule_interval=None,  # This DAG is manually triggered, not scheduled
    start_date=datetime(2023, 9, 22),
    catchup=False,
)
def start_etl():

    @task(multiple_outputs=True)
    def get_jobs_from_database():
        cassandra_manager = CassandraSessions(keyspace='job_data')
        jobs = cassandra_manager.retrieve_jobs_last_day()
        return {'jobs':jobs}

  
    @task()
    def generate_resume(result):
        cnt=1
        for v in result:
            for key in v:
                v[key]=str(v[key])
            resume_gen(v['job_title'],",".join(v["skills"]),v['employer_name'],v['job_apply_link'],v['job_tag'],cnt)
            cnt+=1
            

    jobs=get_jobs_from_database()
    generate_resume(jobs['jobs'])
    
start_etl() 