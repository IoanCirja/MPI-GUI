import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserQuota {
  max_processes_per_user?: number;
  max_processes_per_node_per_user?: number;
  max_running_jobs?: number;
  max_pending_jobs?: number;
  max_job_time?: number;
  allowed_nodes?: number;
  max_nodes_per_job?: number;
  max_total_jobs?: number;
}


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
