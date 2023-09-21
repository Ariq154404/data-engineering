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
from csndra import CassandraSession
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
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
    default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Instantiate a DAG
    dag = DAG(
    'job_extraction_dag',
    default_args=default_args,
    description='A DAG to extract job details',
    schedule_interval=None,  # This DAG is manually triggered, not scheduled
    start_date=datetime(2023, 9, 20),
    catchup=False,
)

# Define the Python functions as tasks
#     load_llm_task = PythonOperator(
#     task_id='load_llm_task',
#     python_callable=load_llm,
#     op_args=['gpt-3.5-turbo'],  # model name argument
#     dag=dag,
# )

#     extract_keyword_task = PythonOperator(
#     task_id='extract_keyword_task',
#     python_callable=extract_keyword,
#     provide_context=True,
#     dag=dag,
# )



#     val_post_process_task = PythonOperator(
#     task_id='val_post_process_task',
#     python_callable=val_post_process,
#     provide_context=True,
#     dag=dag,
# )

    extract_result_for_jobs_task = PythonOperator(
    task_id='extract_result_for_jobs_task',
    python_callable=extract_result_for_jobs,
    op_args=['data scientist'],
    dag=dag,
  )

# Set the task dependencies
    # load_llm_task >> extract_keyword_task >> val_post_process_task >> extract_result_for_jobs_task

    
    # result=extract_result_for_jobs("data scientist")
    # print(len(result))
    # v=result[0]
    # ks=['coding abstracting', 'coding guidelines', 'coding expertise', 'ehr proficiency', 'paper proficiency', 'communication skills', 'privacy comprehension', 'medical coding', 'assignment methodology', 'coding, abstracting', 'hospital it', 'computer proficiency']
    # for v in result:
    #     resume_gen(v['job_title'],",".join(v["skills"]),v['employer_name'],v['job_apply_link'])
    # CassandraSession
    # result={'employer_name': 'Hamilton Health Sciences', 'job_employment_type': 'FULLTIME', 'job_title': 'Coding Data Analyst', 'job_apply_link': 'https://ca.linkedin.com/jobs/view/coding-data-analyst-at-hamilton-health-sciences-3720757018', 'job_description': "The Health Information Management Professional is responsible for the coding and abstracting of records of personal health information in accordance with CIHI guidelines and standards and other relevant guidelines such as CCO\n\n(Cancer Care Ontario). The individual is responsible to ensure that data quality activities are carried out prior to records being submitted at month end. The individual will have excellent understanding of the CIHI coding guidelines\n\nand standards. The HIM professional will be able to work independently and be well organized and able to prioritize workload to ensure quarterly deadlines are met. The individual will have excellent knowledge of coding and abstracting\n\nsoftware and experience in the electronic health record environment as well as a paper-based system. The individual will demonstrate flexibility and be adaptable, demonstrating initiative, identify opportunities for improvement and have excellent communication skills. The individual will maintain patient confidentiality and have knowledge and understanding of privacy principles.\n• Graduate of a recognized Health Information Management Program\n• Certified with Canadian College of Health Information Management and must be an active member in good standing\n• Member of the Ontario Health Record Association is preferred.\n• Experience in ICD-10/CCI coding system and CMG, RIW assignment methodology.\n• Experience with coding and abstracting software preferably Med2020\n• Minimum of one year experience in coding and abstracting all module preferred.\n• Experience in an electronic health record environment as well as a paper-based system\n• Experience in hospital information systems preferably Meditech, MosaiQ, OPIS\n• Computer proficiency in the MS-Suite of Windows applications\n• Excellent communication skills and good judgment\n• Self-directed and the ability to work independently and under occasional interruptions\n\nAs a condition of employment, you are required to submit proof of full COVID-19 vaccination to Employee Health Services.\n\nJob\n\nAdministrative/Service\n\nPrimary Location\n\nOntario-Hamilton\n\nThis position will be located at\n\nHamilton General Hospital\n\nOrganization\n\nHEALTH RECORDS CORP\n\nStatus\n\nRegular\n\nHours per week\n\n37.5\n\nNumber of Openings\n\n1\n\nUnion Code\n\nNon Union Employees\n\nMinimum Salary\n\n34.5000\n\nMaximum Salary\n\n44.2300\n\nPost Date\n\nSep 19, 2023, 12:00:00 AM\n\nOct 9, 2023, 11:59:00 PM\n\nUnit Summary\n\nInformation Support includes the following departments: Health Records and Transcription, Patient Registration, Decision Support Services, Financial Planning and Analysis. Information Support facilitates the creation of a knowledge rich\n\nenvironment for making timely and informed tactical and strategic decisions and maximizing value of care and services provided. It provides accurate, timely, useful information for making decisions based on evidence to help deliver\n\nappropriate patient care. Also provides the expertise in analyzing and interpreting data and presenting and educating the corporation on this information.\n\nSchedule Work Hours\n\nDays/Evenings/Nights\n\nGuidelines\n\nHamilton Health fosters a culture of patient and staff safety, whereby all employees are guided by our Mission, Vision, Values, and Values Based Code of Conduct. Hamilton Health Sciences is a teaching hospital and all staff and physicians are expected to support students and other learners.\n\nTo be considered for this opportunity applicants must apply during the posting period. All internal and external applicants may ONLY apply via the Careers website.\n\nHamilton Health Sciences is an equal opportunity employer and we will accommodate any needs under the Canadian Charter of Rights and Freedom, Accessibility for Ontarians with Disabilities Act and the Ontario Human Rights Code. Hiring processes will be modified to remove barriers to accommodate those with disabilities, if requested. Should any applicant require accommodation through the application processes, please contact the Human Resources Operations at 905-521-2100, Ext. 46947 for assistance. If the applicant requires a specific accommodation because of a disability during an interview, the applicant will need to advise the hiring manager when scheduling the interview and the appropriate accommodations can be made.\n\nThis competition is open to all qualified applicants, however, qualified internal applicants will be considered first. Past performance will be considered as part of the selection process. If you are a previous employee of Hamilton Health Sciences, please note: the circumstances around an employee's exit will be considered prior to an offer of employment\n\nProficiency in both Official Languages, French and English, is considered an asset\n\nIf this position is temporary, selection for this position will be as per the outlined Collective Agreements:\n\nArticle 30 (k), CUPE Collective Agreement\n\nArticle 10.7 (d), ONA Collective Agreement\n\nArticle 13.01 (b) (ii), OPSEU 273 Collective Agreement\n\nArticle 14.04, OPSEU 209 Collective Agreement\n\nArticle 2.07 and Article 13, PIPSC RT Collective Agreement.", 'job_posted_at_timestamp': 1695112322, 'job_posted_at_datetime_utc': '2023-09-19T08:32:02.000Z', 'skills': ['coding abstracting', 'coding guidelines', 'coding expertise', 'ehr proficiency', 'paper proficiency', 'communication skills', 'privacy comprehension', 'medical coding', 'assignment methodology', 'coding, abstracting', 'hospital it', 'computer proficiency']}
    # cassandra_manager = CassandraSession(keyspace='job_data')
    # cassandra_manager.insert_job_data(result)
    # jobs = cassandra_manager.retrieve_jobs_last_day()
    