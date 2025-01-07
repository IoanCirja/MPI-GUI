import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UserService } from '../services/user.service';
import { jwtDecode } from 'jwt-decode';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm: FormGroup;
  hidePassword: boolean = true; 

  constructor(private fb: FormBuilder, private router: Router, private userService: UserService) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required]], 
      password: ['', [Validators.required]]
    });
  }

  onSubmit() {
    if (this.loginForm.valid) {
      this.userService.login(this.loginForm.value).subscribe({
        next: (response: any) => {
          const token = response.token;
          localStorage.setItem('authToken', token);

          
  
          const decodedToken: any = jwtDecode(token);
          const userData = {
            email: decodedToken.email,
            username: decodedToken.username,
          }
          localStorage.setItem('userData', JSON.stringify(userData));
  
          this.router.navigate(['/jobs/upload-job']);
        },
        error: (error) => {
          console.error('Login failed:', error);
        }
      });
    }
  }

 
  switchToSignup() {
    this.router.navigate(['/auth/signup']); 
  }

  togglePasswordVisibility() {
    this.hidePassword = !this.hidePassword; 
  }
}
