from pydantic import BaseModel

class JobUploadDTO(BaseModel):
    jobName: str
    jobDescription: str

    beginDate: str
    endDate: str

    fileName: str
    fileContent: str

    hostFile: str
    hostNumber: int

    numProcesses: int
    allowOverSubscription: bool

    environmentVars: str
    displayMap: bool
    rankBy: str
    mapBy: str

    status: str
    output: str

    # scheduled: bool
    # scheduledDate: str
    #
