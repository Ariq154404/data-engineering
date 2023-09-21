from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.policies import RetryPolicy
from datetime import datetime, timedelta

class CassandraSession:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CassandraSession, cls).__new__(cls)
        return cls._instance

    def __init__(self, keyspace: str, nodes: list = ['localhost']):
        self.keyspace = keyspace
        self.cluster = Cluster(nodes)
        self.session = self.cluster.connect()
        self._create_keyspace()
        self.session.set_keyspace(self.keyspace)
        self._create_schema()

    def _create_keyspace(self):
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {self.keyspace} 
        WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }};
        """
        self.session.execute(query)

    def _create_schema(self):
        query = """
        CREATE TABLE IF NOT EXISTS job_details (
            job_title TEXT,
            job_posted_at_datetime_utc TIMESTAMP,
            employer_name TEXT,
            job_employment_type TEXT,
            job_apply_link TEXT,
            job_description TEXT,
            job_posted_at_timestamp BIGINT,
            skills LIST<TEXT>,
            PRIMARY KEY (job_title, job_posted_at_datetime_utc)
        );
        """
        self.session.execute(query)

    def insert_job_data(self, job_data: dict):
        job_datetime = datetime.fromisoformat(job_data['job_posted_at_datetime_utc'].replace('Z', '+00:00'))
        query = """
        INSERT INTO job_details (job_title, job_posted_at_datetime_utc, employer_name, job_employment_type, 
                                 job_apply_link, job_description, job_posted_at_timestamp, skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        self.session.execute(query, (job_data['job_title'], 
                                     job_datetime,
                                     job_data['employer_name'], 
                                     job_data['job_employment_type'], 
                                     job_data['job_apply_link'], 
                                     job_data['job_description'], 
                                     job_data['job_posted_at_timestamp'], 
                                     job_data['skills']))

    def retrieve_jobs_last_day(self):
        query = """
        SELECT * FROM job_details WHERE job_posted_at_datetime_utc > %s ALLOW FILTERING;
        """
        one_day_ago = datetime.utcnow() - timedelta(days=3)
        print(one_day_ago)
        #print("SS",SimpleStatement(query, (one_day_ago,)))
        rows = self.session.execute(query, [one_day_ago])
        return [row._asdict() for row in rows]

    def close(self):
        self.session.shutdown()
        self.cluster.shutdown()

# Usage:
# cassandra_manager = CassandraSession(keyspace='job_data')
# Insert and retrieve jobs as before
