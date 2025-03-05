export interface Job {
    jobName: string;
    jobDescription: string;
    beginDate: string;
    endDate: string;
    fileName: string;
    fileContent: string;
    hostFile: string;
    numProcesses: number;
    allowOverSubscription: boolean;
    environmentVars: string;
    displayMap: boolean;
    rankBy: string;
    mapBy: string;
    status: string;
    output: string;
  }