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
