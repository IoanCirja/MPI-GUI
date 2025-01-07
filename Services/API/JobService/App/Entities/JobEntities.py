from pydantic import BaseModel
class JobEntity(BaseModel):
    jobName : str
    jobDescription : str
    lastExecutionDate : str
    numProcesses : int
    allowOverSubscription : bool
    file: str
    hostfile: str
    command: str
    output: str
    status: str
