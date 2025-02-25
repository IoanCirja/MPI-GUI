import { Injectable, OnDestroy } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate, OnDestroy {
  private storageListener: any;

  constructor(private router: Router) {
    this.addStorageEventListener();
  }

  canActivate(): Observable<boolean> | Promise<boolean> | boolean {
    return this.isTokenValid();
  }

  private isTokenValid(): boolean {
    const userData = localStorage.getItem('userData');
    const token = userData ? JSON.parse(userData).token : null;

    console.log('Token:', token);

    if (!token) {
      this.router.navigate(['/auth/login']);
      return false;
    }

    try {
      const decodedToken: any = jwtDecode(token);
      const expirationDate = decodedToken.exp * 1000;
      const currentDate = new Date().getTime();

      if (currentDate >= expirationDate) {
        this.router.navigate(['/auth/login']);
        return false;
      }

      return true;
    } catch (error) {
      console.error('Invalid token format', error);
      this.router.navigate(['/auth/login']);
      return false;
    }
  }

  private addStorageEventListener(): void {
    this.storageListener = (event: StorageEvent) => {
      if (event.key === 'userData') {
        if (!this.isTokenValid()) {
          this.router.navigate(['/auth/login']);
        }
      }
    };
    window.addEventListener('storage', this.storageListener);
  }

  ngOnDestroy(): void {
    window.removeEventListener('storage', this.storageListener);
  }
}
