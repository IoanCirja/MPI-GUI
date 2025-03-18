import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from './User';

@Injectable({
  providedIn: 'root',
})
export class AdminService {

  private usersUrl = 'http://127.0.0.1:8001/api/admin/users';

  constructor(private http: HttpClient) {}

  getAllUsers(): Observable<{ users: User[] }> {
    return this.http.get<{ users: User[] }>(this.usersUrl);
  }

  updateUser(userId: number, payload: Partial<User>): Observable<any> {
    const url = `${this.usersUrl}/${userId}`;
    return this.http.patch(url, payload);
  }
}
