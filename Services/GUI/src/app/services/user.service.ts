import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Login, SignUp } from '../models/Auth';
import { BehaviorSubject, catchError, Observable, tap } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private signupUrl = 'http://localhost:8000/api/signup/';
  private loginUrl = 'http://localhost:8000/api/login/';

  constructor(private http: HttpClient) {}

  private userSubject: BehaviorSubject<any> = new BehaviorSubject<any>(
    JSON.parse(localStorage.getItem('userData') || 'null')
  );

  setUser(user: any) {
    this.userSubject.next(user);
  }

  getUser() {
    return this.userSubject.asObservable();
  }

  signup(user: SignUp) {
    return this.http.post<SignUp>(this.signupUrl, user).pipe(
      tap((response) => {}),
      catchError((error) => {
        throw error;
      })
    );
  }

  login(user: Login): Observable<any> {
    return this.http.post<any>(this.loginUrl, user).pipe(
      tap((response: any) => {
        const decodedToken: any = jwtDecode(response.token);
        const userData = {
          token: response.token,
          email: decodedToken.email,
          username: decodedToken.username,
          rights: decodedToken.rights
        };

        localStorage.setItem('userData', JSON.stringify(userData));
        this.setUser(userData);
      }),
      catchError((error) => {
        throw error;
      })
    );
  }

  // getProfile() {
  //   return this.http.get<any>(this.profileUrl).pipe(
  //     tap((response) => {
  //       const decodedToken: any = jwtDecode(response.token);
  //       const userData = {
  //         token: response.token,
  //         email: decodedToken.email,
  //         username: decodedToken.username,
  //         max_processes_per_user: decodedToken.max_processes_per_user,
  //         max_parallel_jobs_per_user: decodedToken.max_parallel_jobs_per_user,
  //         max_jobs_in_queue: decodedToken.max_jobs_in_queue,
  //         max_memory_usage_per_user_per_cluster: decodedToken.max_memory_usage_per_user_per_cluster,
  //         max_memory_usage_per_process: decodedToken.max_memory_usage_per_process,
  //         max_allowed_nodes: decodedToken.max_allowed_nodes,
  //         max_job_time: decodedToken.max_job_time,
  //         rights: decodedToken.rights
  //       };

  //       localStorage.setItem('userData', JSON.stringify(userData));

  //       this.setUser(userData);
  //       this.setupAutoLogout();
  //     }),
  //     catchError((error) => {
  //       this.setUser(null);
  //       this.router.navigate(['/login']);
  //       throw error;

  //     })
  //   );
  // }
  // private setupAutoLogout() {
  //   const userData = JSON.parse(localStorage.getItem('userData') || 'null');
  //   if (userData && userData.token) {
  //     try {
  //       const decodedToken: any = jwtDecode(userData.token);

  //       const issuedAt = decodedToken.iat;
  //       const expirationTime = decodedToken.exp;

  //       const timeUntilExpiration = expirationTime - issuedAt;

  //       if (timeUntilExpiration > 0) {
  //         setTimeout(() => {
  //           this.clearUserData();
  //         }, timeUntilExpiration * 1000);
  //       } else {
  //         this.clearUserData();
  //       }
  //     } catch (error) {
  //       this.clearUserData();
  //     }
  //   }
  // }

  // private clearUserData() {
  //   localStorage.removeItem('userData');
  //   if (this.userSubject) {
  //     this.setUser(null);
  //     this.router.navigate(['/login']);
  //   }
  // }
}
