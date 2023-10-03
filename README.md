
# Automated resume tailoring using langchain

Resume tailoring is a tedious process while applying for jobs. I tried to create a automated resume tailoring pipeline using open ai gpt-3 and gpt-4 with the help of langchain. Given a written essay about your-self. In my case, it is stored in myself.txt, the pipeline is designed to churn tailored resumes based on the job description, personal information and keywords extracted from the jobs. 
 




## Process overview

![Information Shrinking](https://github.com/Ariq154404/data-engineering/blob/main/info_shrink.png)

In order to save API cost , which is determined by the number of input and output token that is proportoinal to the number of words, main essay about personal information is seperate to multiple text files. Each of the files has relaven personal project sorted out based on the pertinance to role and the number of words is kept within 500.

![Architecture](https://github.com/Ariq154404/data-engineering/blob/main/architecture.png)

Initially a ETL pipeline is created as Apache Airflow DAG. This pipeline extracts job description from the API. Then, another task is to extract the keyword skills from the job and create a structure in accordace to the schema and store it in cassandra. Cassandra is chosen as No-sql databse with the capability to sore list of keywords. The partition key here is the title of the data and the primary key within the partition is the date the job was posted which is extracted from the API.

Second DAG retrieves the data within that last day and sends it to llm, which then based on the correct job role , retrieved the job role and churns out resume in latex.

Airflow webserver and cassandra are run as background servers.

![Airflow UI](https://github.com/Ariq154404/data-engineering/blob/main/pipelin_resumegen.png)

The diagram above shows the UI of airflow

![Sample Airflow ETL ](https://github.com/Ariq154404/data-engineering/blob/main/ETL_for_keyword_extraction.png)

The diagram above shows sample ETL DAG in airflow

![Sample Resume ](https://github.com/Ariq154404/data-engineering/blob/main/sample_resume.png)


The image above shows how a sample resume looks like. Whenever the resume generation pipeline DAG is executed, it fills up the folder with tailored resumes

![Sample filtered information](https://github.com/Ariq154404/data-engineering/blob/main/sample_filtered_infor.png)













## Run Locally

Clone the project

```bash
  git clone https://github.com/Ariq154404/data-engineering
```

Create the virtual environment

```bash
  python3.9 -m venv myenv
```

Activate the virtual Environment

```bash
  source myenv/bin/activate
```

Install the dependencies

```bash
  pip install -r requirements.txt
```

Go to the project directory

```bash
  cd dags
```

Run the file to shirnk the information

```bash
  python3 filter_info.py
```
Go back to data engineering folder

Run docker containers in the background 

```bash
  docker-compose up -d
```
Test the cassandra and airflow containers are running by going inside.

In one terminal go inside airflow

```bash
  docker exec -it data-engineering_webserver_1  /bin/bash
```
In another terminal go inside cassandra

```bash
  docker exec -it cassandra /bin/bash
```
Run airflow server

```bash
  http://localhost:8080
```
When done running the dags, shown down the docker containers

```bash
  docker-compose down
```



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file. 
Create .env file with the following command

```bash
  touch .env
```
`openai_key`

`jsearch_api`


## Acknowledgements

 - [Docker compose for airflow and cassandra](https://github.com/airscholar/e2e-data-engineering/blob/main/docker-compose.yml)
 
- [Rapid API jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)

- [Open AI api ](https://platform.openai.com/docs/introduction)

## Tech Stack

**ETL:**  Apache Airflow

**Database:**  Apache cassandra

**llm**  chatgpt, langchain library

