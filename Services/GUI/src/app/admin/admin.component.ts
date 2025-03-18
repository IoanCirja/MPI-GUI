import { Component, OnInit } from '@angular/core';
import { AdminService } from './admin.service';
import { User } from './User';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
  imports: [CommonModule],
})
export class AdminComponent implements OnInit {

  users: User[] = [];
  errorMessage: string = '';

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.fetchAllUsers();
  }

  fetchAllUsers(): void {
    this.adminService.getAllUsers().subscribe(
      (response) => {
        this.users = response.users;
      },
      (error) => {
        this.errorMessage = 'Failed to load users. Make sure you are logged in as an admin.';
        console.error(error);
      }
    );
  }

  updateUser(userId: number, field: string, value: any): void {
    const payload = { [field]: value };
    
    this.adminService.updateUser(userId, payload).subscribe(
      () => {
        console.log(`User ${userId} updated successfully.`);
      },
      (error) => {
        console.error(`Failed to update user ${userId}:`, error);
        this.errorMessage = 'Failed to update user. Please try again.';
      }
    );
  }
}
