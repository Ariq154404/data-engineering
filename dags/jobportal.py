from abc import ABC, abstractmethod
import requests
import json
class JobPortal(ABC):

    @abstractmethod
    def fetch_job_description(self, job_title: str):
        pass

class Jsearch(JobPortal):

    def __init__(self):
        self.url = "https://jsearch.p.rapidapi.com/search"

        self.headers = {
	"X-RapidAPI-Key": "bddea5728dmshb9cc1671c210a7cp1417d7jsn533948b366bd",
	"X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                       }
    def filter_dic(self,res_dic,tag):
        keys_list=['employer_name','job_employment_type','job_title','job_apply_link','job_description','job_posted_at_timestamp','job_posted_at_datetime_utc']
        lst=[{key: v[key] for key in keys_list if key in v} for v in res_dic["data"] ]
        for v in lst:
            v['tag']=tag
        return lst[:2]
            
        
    def fetch_job_description(self, job_title: str,tag: str):
        querystring = {"query":job_title,"page":"1","num_pages":"1","date_posted":"today","employment_type":"FULLTIME","job_requirements":"under_3_years_experience","country":"CA"}

        response = requests.get(self.url, headers=self.headers, params=querystring)

        # Assuming the job description is in the response. 
        # The structure depends on the API's actual response format.
        res_dic=response.json()
        # res_dic=jres.loads()
        return self.filter_dic(res_dic,tag)

# Usage:
# indeed_portal = Indeed()
# description = indeed_portal.fetch_job_description("data scientist")
# print(description)
