import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from './User';
import { Suspension } from './Suspension';
import { Job } from '../job-poster/models/Job';

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  private usersUrl = 'http://127.0.0.1:8001/api/admin/users/';
  private suspendUrl = 'http://127.0.0.1:8001/api/admin/suspend/';
  private suspensionsUrl = 'http://127.0.0.1:8001/api/admin/suspensions/';
  private adminJobsUrl = 'http://127.0.0.1:8002/api/jobs/admin';    // ← new

  constructor(private http: HttpClient) {}

  getAllUsers(): Observable<{ users: User[] }> {
    return this.http.get<{ users: User[] }>(this.usersUrl);
  }


  updateUsers(payload: { users: Partial<User>[] }): Observable<{ message: string }> {
    const url = `${this.usersUrl}`;
    return this.http.patch<{ message: string }>(url, payload);
  }

  getAllSuspensions(): Observable<{ suspensions: Suspension[] }> {
    return this.http.get<{ suspensions: Suspension[] }>(this.suspensionsUrl);
  }

  suspendUser(payload: { user_id: string; suspend_time: number }): Observable<{ message: string; user: User }> {
    return this.http.post<{ message: string; user: User }>(this.suspendUrl, payload);
  }

  removeSuspension(payload: { user_id: string, suspension_id: string }): Observable<{ message: string }> {
    const url = `${this.suspensionsUrl}`; 
    return this.http.delete<{ message: string }>(url, { body: payload });
  }

    getAllJobsAdmin(): Observable<Job[]> {
    return this.http.get<Job[]>(this.adminJobsUrl);
  }
  
  
}
