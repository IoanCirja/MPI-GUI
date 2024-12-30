import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms'; 
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component'; 
import { SignupComponent } from './signup/signup.component';
import { HttpClientModule } from '@angular/common/http';
import { UserService } from './services/user.service';

const routes: Routes = [
  { path: 'login', component: LoginComponent },    
  { path: 'signup', component: SignupComponent },  
  { path: '', redirectTo: 'login', pathMatch: 'full' }
];

@NgModule({
  declarations: [
    LoginComponent, 
    SignupComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule, 
    HttpClientModule, 
    RouterModule.forChild(routes)
  ],
  providers: [UserService],
  exports: [RouterModule]
})
export class AuthModule { }
