import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class FileUploadService {
  private apiUrl = 'http://127.0.0.1:8000/api/upload/';

  constructor(private http: HttpClient) {}

  uploadFile(file: File, numProcesses: number, allowOverSubscription:boolean, hostifle: File): Observable<any> {
    const formData = new FormData();
    formData.append('numProcesses', numProcesses.toString());
    formData.append('file', file);
    formData.append('allowOverSubscription', allowOverSubscription.toString());
    formData.append('hostfile', hostifle);
 


    return this.http.post(this.apiUrl, formData);
  }
}
