import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class FileUploadService {
  private apiUrl = 'http:

  constructor(private http: HttpClient) {}

  uploadFile(file: File, numProcesses: number): Observable<any> {
    const formData = new FormData();
    formData.append('numProcesses', numProcesses.toString()); 
    formData.append('file', file);


    return this.http.post(this.apiUrl, formData);
  }
}
