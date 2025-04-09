import { Component, OnInit } from '@angular/core';
import { AdminService } from './admin.service';
import { User } from './User';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

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
  constructor(private adminService: AdminService) {}
  suspensions: any[] = [];


  ngOnInit(): void {
    this.fetchAllUsers();
  }

  fetchAllUsers(): void {
    this.adminService.getAllUsers().subscribe(
      (response) => {
        this.users = response.users;
        console.log('Fetched users:', this.users); 
      },
      (error) => {
        this.errorMessage = 'Failed to load users. Make sure you are logged in as an admin.';
        console.error('Error fetching users:', error); 
      }
    );
  }

  
  markAsModified(userId: string): void {
    console.log(`User ${userId} marked as modified`); 
    this.modifiedUsers.add(userId);
  }

  
  isModified(userId: string): boolean {
    return this.modifiedUsers.has(userId);
  }

  pushChanges(): void {
    const modifiedUsersData = this.users.filter(user => this.isModified(user.id)).map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        rights: user.rights,
        max_processes_per_user: user.max_processes_per_user,
        max_parallel_jobs_per_user: user.max_parallel_jobs_per_user,
        max_jobs_in_queue: user.max_jobs_in_queue,
        max_memory_usage_per_user_per_cluster: user.max_memory_usage_per_user_per_cluster,
        max_memory_usage_per_process: user.max_memory_usage_per_process,
        max_allowed_nodes: user.max_allowed_nodes,
        max_job_time: user.max_job_time
    }));

    const payload = { users: modifiedUsersData };

    this.adminService.updateUsers(payload).subscribe(
        () => {
            console.log('Users updated successfully');
            this.modifiedUsers.clear();  
        },
        (error) => {
            console.error('Error updating users:', error);
            this.errorMessage = 'Failed to update users. Please try again.';
        }
    );
}

fetchSuspensions(): void {
  this.adminService.getAllSuspensions().subscribe(
    (response) => {
      this.suspensions = response.suspensions;
    },
    (error) => {
      this.errorMessage = 'Failed to load suspensions.';
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
    },
    (error) => {
      this.errorMessage = 'Failed to suspend user.';
    }
  );
}
}
