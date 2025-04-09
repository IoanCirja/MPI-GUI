export interface User {
    id: string;
    username: string;
    email: string;
    rights?: string;
    max_processes_per_user?: number;
    max_parallel_jobs_per_user?: number;
    max_jobs_in_queue?: number;
    max_memory_usage_per_user_per_cluster?: string;
    max_memory_usage_per_process?: string;
    max_allowed_nodes?: number;
    max_job_time?: string;
    suspensions?: any;
  }
  