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

  uploadFile(file: File, numProcesses: number, allowOverSubscription:boolean, hostifle: File, jobName:string, jobDescription:string, lastExecutionTime:string): Observable<any> {
    const formData = new FormData();
    formData.append('numProcesses', numProcesses.toString());
    formData.append('file', file);
    formData.append('allowOverSubscription', allowOverSubscription.toString());
    formData.append('hostfile', hostifle);
    formData.append('jobName', jobName);
    formData.append('jobDescription', jobDescription);
    formData.append('lastExecutionTime', lastExecutionTime);

    const token = localStorage.getItem('authToken');

    const headers = new HttpHeaders({
      Authorization: token ? `Bearer ${token}` : '',
    });
 


    return this.http.post(this.apiUrl, formData, { headers });
  }

  getJobStatus(): Observable<any> {
    const token = localStorage.getItem('authToken');
    const headers = new HttpHeaders({
      Authorization: token ? `Bearer ${token}` : '',
    });

    return this.http.get(this.jobUrl, { headers });
  }

}
