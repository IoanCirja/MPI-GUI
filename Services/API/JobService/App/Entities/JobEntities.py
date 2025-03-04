from pydantic import BaseModel
class JobEntity(BaseModel):
    id: str
    jobName : str
    jobDescription : str
    beginDate: str
    endDate: str
    numProcesses : int
    allowOverSubscription : bool
    file: str
    hostfile: str
    command: str
    output: str
    status: str
    environmentVars: str
    displayMap: str
    rankBy: str
    mapBy:str