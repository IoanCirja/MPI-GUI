import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Job } from '../models/Job';

@Injectable({
  providedIn: 'root',
})
export class FileUploadService {
  private apiUrl = 'http://127.0.0.1:8000/api/upload/';
  private jobUrl = 'http://localhost:8000/api/jobs/';

  constructor(private http: HttpClient) {}

  uploadFile(job: Job): Observable<any> {
    console.log("payload", JSON.stringify(job));
    return this.http.post(this.apiUrl, JSON.stringify(job), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
    

  getJobStatus(): Observable<any> {

    return this.http.get(this.jobUrl);
  }

  killJob(jobId: string): Observable<any> {
    const url = `http://localhost:8000/api/jobs/${jobId}/kill`;

  
    return this.http.post(url, {});
  }
  
}
