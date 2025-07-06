import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Suspension } from '../models/Suspension';
import { Job, UserJob } from '../models/Job';
import { AdminService } from '../services/admin.service';
import { User } from '../models/User';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
  imports: [CommonModule, FormsModule],
})
export class AdminComponent implements OnInit {

  users: User[] = [];
  errorMessage: string = '';
  modifiedUsers: Set<string> = new Set();
  showSuspendModal: boolean = false;
  selectedUser: User | null = null;
  suspendTime: number = 10;
  currentDate: string = new Date().toISOString();
  suspensions: Suspension[] = [];
  successMessage: string = '';
  showSuccessPopup: boolean = false;
  adminJobs: UserJob[] = [];

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.fetchAllUsers();
    this.fetchSuspensions();
    this.fetchAllJobsAdmin();
  }


    decodeBase64(encodedString: string): string {
    try {
      return atob(encodedString);
    } catch (e) {
      return encodedString;
    }
  }

  downloadExecutable(name: string, content: string): void {
    const decodedContent = this.decodeBase64(content);

    const blob = new Blob(
      [new Uint8Array(decodedContent.split('').map((c) => c.charCodeAt(0)))],
      { type: 'application/x-msdownload' }
    );

    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    link.click();
  }

  downloadHostfile(encodedHostfile: string): void {
    const decodedHostfile = this.decodeBase64(encodedHostfile);
    const blob = new Blob([decodedHostfile], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'hostfile.txt';
    link.click();
  }

  fetchAllJobsAdmin() {
    this.adminService.getAllJobsAdmin().subscribe({
      next: (jobs) => (this.adminJobs = jobs),
      error: (err) => console.error('Could not load all jobs:', err),
    });
  }
  isAllValid(): boolean {
    return this.users.every(
      (user) =>
        this.isValidUsername(user.username) &&
        this.isValidEmail(user.email) &&
        this.isValidMaxProcesses(user.max_processes_per_user) &&
        this.isValidMaxProcessesPerNode(user.max_processes_per_node_per_user) &&
        this.isValidMaxRunningJobs(user.max_running_jobs) &&
        this.isValidMaxPendingJobs(user.max_pending_jobs) &&
        this.isValidMaxJobTime(user.max_job_time) &&
        this.isValidAllowedNodes(user.allowed_nodes) &&
        this.isValidMaxNodesPerJob(user.max_nodes_per_job) &&
        this.isValidMaxTotalJobs(user.max_total_jobs)
    );
  }

  isValidUsername(username: string): boolean {
    return Boolean(username && username.length > 0);
  }

  isValidEmail(email: string): boolean {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  }

  isValidMaxProcesses(maxProcesses: number): boolean {
    return maxProcesses >= 1 && maxProcesses <= 1000;
  }

  isValidMaxProcessesPerNode(maxProcesses: number): boolean {
    return maxProcesses >= 1 && maxProcesses <= 1000;
  }

  isValidMaxRunningJobs(maxRunningJobs: number): boolean {
    return maxRunningJobs >= 1 && maxRunningJobs <= 1000;
  }

  isValidMaxPendingJobs(maxPendingJobs: number): boolean {
    return maxPendingJobs >= 1 && maxPendingJobs <= 1000;
  }

  isValidMaxJobTime(maxJobTime: number): boolean {
    return maxJobTime >= 1 && maxJobTime <= 10000000;
  }

  isValidAllowedNodes(allowedNodes: string): boolean {
    const nodesPattern = /^C[0-9]{2}$/;
    return allowedNodes
      .split(',')
      .every((node) => nodesPattern.test(node.trim()));
  }

  isValidMaxNodesPerJob(maxNodes: number): boolean {
    return maxNodes >= 1 && maxNodes <= 21;
  }

  isValidMaxTotalJobs(maxTotalJobs: number): boolean {
    return maxTotalJobs >= 1 && maxTotalJobs <= 1000;
  }

  fetchAllUsers(): void {
    this.adminService.getAllUsers().subscribe(
      (response) => {
        this.users = response.users;
      },
      (error) => {
        this.errorMessage =
          'Failed to load users. Make sure you are logged in as an admin.';
      }
    );
  }

  markAsModified(userId: string): void {
    this.modifiedUsers.add(userId);
  }

  isModified(userId: string): boolean {
    return this.modifiedUsers.has(userId);
  }


  removeSuspension(suspension: Suspension): void {
    if (!confirm('Are you sure you want to remove this suspension?')) {
      return;
    }

    const payload = {
      user_id: suspension.user_id,
      suspension_id: suspension.id,
    };

    this.adminService.removeSuspension(payload).subscribe(
      () => {
        this.fetchSuspensions();
      },
      (error) => {
        this.errorMessage = 'Failed to remove suspension.';
      }
    );
  }

  pushChanges(): void {
    const modifiedUsersData = this.users
      .filter((user) => this.isModified(user.id))
      .map((user) => ({
        id: user.id,
        username: user.username,
        email: user.email,
        max_processes_per_user: user.max_processes_per_user,
        max_processes_per_node_per_user: user.max_processes_per_node_per_user,
        max_running_jobs: user.max_running_jobs,
        max_pending_jobs: user.max_pending_jobs,
        max_job_time: user.max_job_time,
        allowed_nodes: user.allowed_nodes,
        max_nodes_per_job: user.max_nodes_per_job,
        max_total_jobs: user.max_total_jobs,
      }));

    const payload = { users: modifiedUsersData };

    this.adminService.updateUsers(payload).subscribe(
      () => {
        this.modifiedUsers.clear();
        this.successMessage = 'Changes successfully applied!';
        this.showSuccessPopup = true;
        setTimeout(() => {
          this.showSuccessPopup = false;
        }, 3000);
      }
    );
  }

  fetchSuspensions(): void {
    this.adminService.getAllSuspensions().subscribe(
      (response) => {
        this.suspensions = response.suspensions;
      }
    );
  }

  openSuspendModal(user: User): void {
    this.selectedUser = user;
    this.showSuspendModal = true;
  }

  closeSuspendModal(): void {
    this.showSuspendModal = false;
  }

  confirmSuspend(): void {
    if (!this.selectedUser) return;

    const payload = {
      user_id: this.selectedUser.id,
      suspend_time: this.suspendTime,
    };

    this.adminService.suspendUser(payload).subscribe(
      () => {
        this.fetchSuspensions();
        this.closeSuspendModal();
      }
    );
  }
}
