from pydantic import BaseModel

class JobDTO(BaseModel):
    jobName: str
    jobDescription: str
    lastExecutionDate: str
    numProcesses: int
    allowOverSubscription: bool
    file: str
    hostfile: str
    command: str
    output: str
    status:str
