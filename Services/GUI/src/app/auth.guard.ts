import { Injectable, OnDestroy } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';
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

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {
    return this.isTokenValid(state.url);
  }

  private isTokenValid(url: string): boolean {
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
      const userRights = decodedToken.rights || 'base';


      if (currentDate >= expirationDate) {
        this.router.navigate(['/auth/login']);
        return false;
      }
      

      if (url.startsWith('/auth')) {
        console.log('URL:', url);
        this.router.navigate(['/']);
        return false;
      }


      if (userRights === 'admin' && !url.startsWith('/admin')) {
        this.router.navigate(['/admin']);
        return false;
      }

      if (userRights === 'base' && url.startsWith('/admin')) {
        this.router.navigate(['/']);
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
        if (!this.isTokenValid(window.location.pathname)) {
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
