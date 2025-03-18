import { Injectable, OnDestroy } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  Router,
  RouterStateSnapshot,
} from '@angular/router';
import { Observable } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

@Injectable({
  providedIn: 'root',
})
export class NonAuthGuard implements CanActivate {
  constructor(private router: Router) {}
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    return this.isTokenValid(state.url);
  }

  private isTokenValid(url: string): boolean {
    const userData = localStorage.getItem('userData');
    const token = userData ? JSON.parse(userData).token : null;

    try {
      if (!token) {
        return true;
      } else {
        this.router.navigate(['/']);

        return false;
      }
    } catch (error) {
      console.error('Invalid token format', error);
      return false;
    }
  }
}
