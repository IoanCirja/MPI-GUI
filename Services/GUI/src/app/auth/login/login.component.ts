import { Component } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { UserService } from '../../services/user.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  imports: [ReactiveFormsModule, CommonModule],
  styleUrls: ['./login.component.css'],
})
export class LoginComponent {
  loginForm: FormGroup;
  hidePassword: boolean = true;
  errorMessages: string[] = [];
  loginButtonDisabled: boolean = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private userService: UserService
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required]],
      password: ['', [Validators.required]],
    });
  }

  ngOnInit(): void {}

  ngOnDestroy(): void {
    if (this.errorMessages.length > 0) {
      this.clearErrorMessages();
    }
  }

  onSubmit() {
    if (this.loginForm.valid) {
      this.userService.login(this.loginForm.value).subscribe({
        next: () => {
          this.router.navigate(['/jobs/upload-job']);
        },
        error: (error) => {
          if (error?.error?.detail) {
            this.processErrorDetails(error.error.detail);
          } else {
            this.processErrorDetails('An error occurred');
          }

          this.loginButtonDisabled = true;
          setTimeout(() => {
            this.loginButtonDisabled = false;
          }, 1000);
        },
      });
    }
  }

  processErrorDetails(errorDetails: any) {
    this.errorMessages = [];
    this.loginForm.setErrors(null);

    if (Array.isArray(errorDetails)) {
      errorDetails.forEach((err: any) => {
        const message = err.ctx && err.ctx.reason ? err.ctx.reason : err.msg;
        this.errorMessages.push(message);
        this.setErrorMessage(err.loc[1], message);
      });
    } else if (errorDetails) {
      this.errorMessages.push(errorDetails);
    }
  }

  setErrorMessage(field: string, message: string) {
    const control = this.loginForm.get(field);
    if (control) {
      control.setErrors({ serverError: message });
    }
    this.autoCloseErrorPopup();
  }

  closeErrorPopup() {
    this.clearErrorMessages();
  }

  clearErrorMessages() {
    this.errorMessages = [];
  }

  autoCloseErrorPopup() {
    setTimeout(() => {
      this.clearErrorMessages();
    }, 5000);
  }

  switchToSignup() {
    this.router.navigate(['/auth/signup']);
  }

  togglePasswordVisibility() {
    this.hidePassword = !this.hidePassword;
  }
}
