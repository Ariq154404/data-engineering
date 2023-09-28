from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.policies import RetryPolicy
from datetime import datetime, timedelta

class CassandraSessions:

    def __init__(self, keyspace: str, nodes: list = ['cassandra_db']):
        self.keyspace = keyspace
        self.cluster = Cluster(nodes)
        self.session = self.cluster.connect()
        self._create_keyspace()
        self.session.set_keyspace(self.keyspace)
        self._create_schema()
        print('Database creation DONE')

    def _create_keyspace(self):
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {self.keyspace} 
        WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }};
        """
        self.session.execute(query)
        print('Created Keyspace')

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
            job_tag TEXT,
            skills LIST<TEXT>,
            PRIMARY KEY (job_title, job_posted_at_datetime_utc)
        );
        """
        self.session.execute(query)
        print("Created Schema")

    def insert_job_data(self, job_data: dict):
        job_datetime = datetime.fromisoformat(job_data['job_posted_at_datetime_utc'].replace('Z', '+00:00'))
        query = """
        INSERT INTO job_details (job_title, job_posted_at_datetime_utc, employer_name, job_employment_type, 
                                 job_apply_link, job_description, job_posted_at_timestamp, job_tag, skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        self.session.execute(query, (job_data['job_title'], 
                                     job_datetime,
                                     job_data['employer_name'], 
                                     job_data['job_employment_type'], 
                                     job_data['job_apply_link'], 
                                     job_data['job_description'], 
                                     job_data['job_posted_at_timestamp'],
                                     job_data['tag'], 
                                     job_data['skills']))
        print("Inserted data")

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
        print("Session shutdouwn")

# Usage:
# cassandra_manager = CassandraSession(keyspace='job_data')
# Insert and retrieve jobs as before
