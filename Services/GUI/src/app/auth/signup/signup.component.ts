import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl } from '@angular/forms';
import { Router } from '@angular/router';
import { UserService } from '../services/user.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  signupForm: FormGroup;
  hidePassword: boolean = true; 
  passwordChecks: boolean[] = [false, false, false]; 

  constructor(private fb: FormBuilder, private router: Router, private userService: UserService) {
    this.signupForm = this.fb.group({
      username: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8), this.passwordValidator.bind(this)]],
      retypePassword: ['', [Validators.required]]
    });

    this.signupForm.get('password')?.valueChanges.subscribe(value => {
      this.validatePassword(value);
    });
  }

  passwordValidator(control: AbstractControl): { [key: string]: boolean } | null {
    const value = control.value;
    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumber = /\d/.test(value);

    if (hasUpperCase && hasLowerCase && hasNumber) {
      return null; 
    }
    return { 'passwordInvalid': true }; 
  }

  validatePassword(value: string) {
    this.passwordChecks[0] = value.length >= 8;
    this.passwordChecks[1] = /\d/.test(value);
    this.passwordChecks[2] = /[a-z]/.test(value) && /[A-Z]/.test(value);
  }

  onSubmit() {
    if (this.signupForm.valid) {
      this.userService.signup(this.signupForm.value).subscribe(() => {
        this.router.navigate(['/auth/login']);
      });
    }
  }

  switchToLogin() {
    this.router.navigate(['/auth/login']);
  }

  togglePasswordVisibility() {
    this.hidePassword = !this.hidePassword;
  }
}
