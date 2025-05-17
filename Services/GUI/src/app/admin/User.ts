import { Suspension } from "./Suspension";

export interface User {
    id: string;
    username: string;
    email: string;
    max_processes_per_user: number; // 1 - 70
    max_processes_per_node_per_user: number; // 1 - 10
    max_running_jobs: number; // 1 - 30
    max_pending_jobs: number; // 1- 30
    max_job_time: number; // 100 - 100000
    allowed_nodes: string; // C00, C01, pana la C20
    max_nodes_per_job: number; // 1 - 20
    max_total_jobs: number; // 100
    suspensions: Suspension[];
  }

