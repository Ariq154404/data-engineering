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
from database import CassandraSessions
from airflow import DAG
from datetime import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.decorators import dag, task

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
def get_api_data(job_title,tag):
    jsearch = Jsearch()
    jobs= jsearch.fetch_job_description(job_title + "in Canada",tag)
    return jobs

    # last_day_job=cassandra_manager.retrieve_jobs_last_day()
    # print('DATA of lst day fetched')
    # print(last_day_job)
    #return last_day_job        
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}
def load_llm(model_name):
        load_dotenv()
    #os.environ.get('openai_key') 
        llm=ChatOpenAI(model=model_name,temperature = 0,
                          openai_api_key =  ,         
                          max_tokens=3000                 
                         ) 
        return llm
@dag(
    dag_id='job_extraction_with_task_flow',
    default_args=default_args,
    description='A DAG to extract job details',
    schedule_interval=None,  # This DAG is manually triggered, not scheduled
    start_date=datetime(2023, 9, 22),
    catchup=False,
)
def start_etl():

    @task(multiple_outputs=True)
    def get_jobs_from_api():
        job_tags=JobTags()
        jtags=job_tags.get_tags()
        #lst=['Machine learning',"Data Science","Software Engineer","Python Developer","Data Engineer"]
        nlst=[]
        for v in jtags:
            nlst+=get_api_data(jtags[v],v)
        print("ALL JOBS",nlst)
        return {'jobs':nlst}

    @task()
    def insert_into_database(results):
        print("Results",results)
        cassandra_manager=CassandraSessions(keyspace='job_data')
        for v in results:
            print("TAAAAG",v['tag'])
            cassandra_manager.insert_job_data(v)
    @task(multiple_outputs=True)
    def extract_keywords_from_jobs(jobs):
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
            results.append(job)
        print("Results",results)
        return {'results':results}

    jobs=get_jobs_from_api()
    results=extract_keywords_from_jobs(jobs['jobs'])
    insert_into_database(results=results['results'])
start_etl() 