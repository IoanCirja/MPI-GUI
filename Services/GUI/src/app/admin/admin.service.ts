import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from './User';

@Injectable({
  providedIn: 'root',
})
export class AdminService {

  private usersUrl = 'http://127.0.0.1:8001/api/admin/users';
  private suspendUrl = 'http://127.0.0.1:8001/api/admin/suspend';
  private suspensionsUrl = 'http://127.0.0.1:8001/api/admin/suspensions';

  constructor(private http: HttpClient) {}

  getAllUsers(): Observable<{ users: User[] }> {
    return this.http.get<{ users: User[] }>(this.usersUrl);
  }

  updateUser(userId: string, payload: Partial<User>): Observable<any> {
    const url = `${this.usersUrl}/${userId}`;
    return this.http.patch(url, payload);
  }

  updateUsers(payload: { users: any[] }): Observable<any> {
    const url = `${this.usersUrl}`;
    return this.http.patch(url, payload);
  }

  getAllSuspensions(): Observable<{ suspensions: any[] }> {
    return this.http.get<{ suspensions: any[] }>(this.suspensionsUrl);
  }

  suspendUser(payload: any): Observable<any> {
    return this.http.post(this.suspendUrl, payload);
  }
}
