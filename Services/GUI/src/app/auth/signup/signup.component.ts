import { Component } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  Validators,
  AbstractControl,
  ReactiveFormsModule,
} from '@angular/forms';
import { Router } from '@angular/router';
import { UserService } from '../../services/user.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  imports: [ReactiveFormsModule, CommonModule],
  styleUrls: ['./signup.component.css'],
})
export class SignupComponent {
  signupForm: FormGroup;
  hidePassword: boolean = true;
  passwordChecks: boolean[] = [false, false, false];
  errorMessages: string[] = [];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private userService: UserService
  ) {
    this.signupForm = this.fb.group({
      username: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(8),
          this.passwordValidator.bind(this),
        ],
      ],
      retypePassword: ['', [Validators.required]],
    });

    this.signupForm.get('password')?.valueChanges.subscribe((value) => {
      this.validatePassword(value);
    });
  }

  passwordValidator(
    control: AbstractControl
  ): { [key: string]: boolean } | null {
    const value = control.value;
    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumber = /\d/.test(value);

    if (hasUpperCase && hasLowerCase && hasNumber) {
      return null;
    }
    return { passwordInvalid: true };
  }

  validatePassword(value: string) {
    this.passwordChecks[0] = value.length >= 8;
    this.passwordChecks[1] = /\d/.test(value);
    this.passwordChecks[2] = /[a-z]/.test(value) && /[A-Z]/.test(value);
  }

  onSubmit() {
    if (this.signupForm.valid) {
      this.userService.signup(this.signupForm.value).subscribe(
        () => {
          this.router.navigate(['/auth/login']);
        },
        (error) => {
          console.log('Signup failed, processing error:', error);
          this.processErrorDetails(error.error.detail);
        }
      );
    } else {
      this.collectFormErrors();
    }
  }

  processErrorDetails(errorDetails: any) {
    console.log('Processing error details:', errorDetails);
    this.errorMessages = [];

    if (Array.isArray(errorDetails)) {
      errorDetails.forEach((err: any) => {
        const message =
          err.msg || (err.ctx && err.ctx.reason) || 'Unknown error';
        this.errorMessages.push(message);
      });
    } else if (errorDetails) {
      this.errorMessages.push(errorDetails);
    }

    this.autoDismissErrors();
  }

  collectFormErrors() {
    this.errorMessages = [];
    Object.keys(this.signupForm.controls).forEach((key) => {
      const control = this.signupForm.get(key);
      if (control?.invalid && (control?.touched || control?.dirty)) {
        for (const error in control.errors) {
          if (control.errors.hasOwnProperty(error)) {
            const errorMessage = this.getErrorMessage(key, error);
            this.errorMessages.push(errorMessage);
          }
        }
      }
    });

    this.autoDismissErrors();
  }

  getErrorMessage(controlName: string, error: string): string {
    const errorMessages: { [key: string]: string } = {
      required: `${controlName} is required.`,
      email: 'Invalid email format.',
      passwordInvalid:
        'Password must contain at least 8 characters, including uppercase, lowercase, and a number.',
    };

    return errorMessages[error] || 'Invalid input';
  }

  autoDismissErrors() {
    setTimeout(() => {
      this.errorMessages = [];
    }, 5000);
  }

  closeErrorPopup() {
    this.errorMessages = [];
  }

  switchToLogin() {
    this.router.navigate(['/auth/login']);
  }

  togglePasswordVisibility() {
    this.hidePassword = !this.hidePassword;
  }
}
