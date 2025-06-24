import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UserQuota } from '../models/UserQuota';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private quotaUrl = 'http://127.0.0.1:8000/api/users/quota';

  constructor(private http: HttpClient) {}

  getUserQuota(): Observable<UserQuota> {
    return this.http.get<UserQuota>(this.quotaUrl);
  }
}
