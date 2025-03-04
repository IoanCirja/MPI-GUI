import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class FileUploadService {
  private apiUrl = 'http://127.0.0.1:8001/api/upload/';
  private jobUrl = 'http://localhost:8001/api/jobs/';

  constructor(private http: HttpClient) {}

  uploadFile(
    file: File,
    numProcesses: number,
    allowOverSubscription: boolean,
    hostifle: File,
    jobName: string,
    jobDescription: string,
    environmentVars: string,
    displayMap: string,
    rankBy: string,
    mapBy: string
  ): Observable<any> {
    const formData = new FormData();
    formData.append('numProcesses', numProcesses.toString());
    formData.append('file', file);
    formData.append('allowOverSubscription', allowOverSubscription.toString());
    formData.append('hostfile', hostifle);
    formData.append('jobName', jobName);
    formData.append('jobDescription', jobDescription);
    formData.append('environmentVars', environmentVars);
    formData.append('displayMap', displayMap);
    formData.append('rankBy', rankBy);
    formData.append('mapBy', mapBy);


    const token = localStorage.getItem('authToken');

    const headers = new HttpHeaders({
      Authorization: token ? `Bearer ${token}` : '',
    });

    return this.http.post(this.apiUrl, formData, { headers });
  }

  getJobStatus(): Observable<any> {

    return this.http.get(this.jobUrl);
  }

  killJob(jobId: string): Observable<any> {
    const url = `http://localhost:8001/api/jobs/${jobId}/kill`;

  
    return this.http.post(url, {});
  }
  
}
