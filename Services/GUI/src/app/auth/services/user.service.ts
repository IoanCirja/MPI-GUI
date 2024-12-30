import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Login, SignUp } from "../models/User";

@Injectable({
    providedIn: 'root'
  })
export class UserService{
    private signupUrl = 'http://localhost:8000/api/users/';
    private loginUrl = 'http://localhost:8000/api/login/';

    constructor(private http: HttpClient){}


    signup(user: SignUp){
        return this.http.post<SignUp>(this.signupUrl, user);
    }
    login(user: Login){
        return this.http.post<Login>(this.loginUrl, user);
    }
}