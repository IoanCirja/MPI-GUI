import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { UserService } from '../services/user.service';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { MatToolbarModule } from '@angular/material/toolbar';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatToolbarModule,
    CommonModule,
    RouterModule,
  ],
  styleUrls: ['./header.component.css'],
})
export class HeaderComponent implements OnInit {
  user: any;

  constructor(
    private router: Router,
    private userService: UserService,
    private cdr: ChangeDetectorRef
  ) {}
  ngOnInit() {
    this.userService.getUser().subscribe((user) => {
      this.user = user;
      this.cdr.detectChanges();

      console.log("User", this.user);
    });

    
  }

  logout() {
    localStorage.removeItem('userData');
    this.userService.setUser(null);
    this.router.navigate(['/login']);
  }
}
