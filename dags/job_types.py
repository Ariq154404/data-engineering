class JobTags:
    def __init__(self):
        self.jobs = [
            "Machine Learning",
            "Data Science",
            "Software Engineer",
            "Python Developer",
            "Data Engineer",
            "Data Analyst"
        ]
        self.tags = {
            "ml": "Machine Learning",
            "ds": "Data Science",
            "se": "Software Engineer",
            "pd": "Python Developer",
            "de": "Data Engineer",
            "da": "Data Analyst"
        }

    def get_tags(self):
        return self.tags