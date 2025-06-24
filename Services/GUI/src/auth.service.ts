import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private PROFILE_URL = 'http://localhost:8000/api/profile/';


  constructor(private http: HttpClient) {}

  validateToken(): Observable<any> {
    return this.http.get<any>(this.PROFILE_URL);
  }
}
