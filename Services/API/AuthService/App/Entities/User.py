from pydantic import BaseModel
class User(BaseModel):
    username: str
    email: str
    password: str
    retypePassword: str


# status base
# max proceses per user
# max paralel jobs per user
# max jobs per user  in a queue
# max memory usage per user per cluster
# max memory usage per proces
# max alowwed nodes
# max job time - kill it when it reaches that
# clear job history
# schedule a job to be recursive
# schedule a job
# uplaod a config for job

# change ndoe alocation if nodes are busy or wait settings option

#add execution time to job in job status


# notify job termination via mail -- settings
# create a curl thing so you can uplaod them from vs code terminal