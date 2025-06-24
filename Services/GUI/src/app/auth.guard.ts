import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';
import { catchError, map, Observable, of } from 'rxjs';
import { AuthService } from '../auth.service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {

  constructor(
    private auth: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> {
    const url = state.url;
    const userData = localStorage.getItem('userData');

    if (url.startsWith('/auth') && !userData) {
      return of(true);
    }

    return this.auth.validateToken().pipe(
      map((payload: any) => {
        if (url.startsWith('/auth')) {
          this.router.navigate(['/dashboard']);
          return false;
        }
        const rights: string = payload.rights ?? 'base';
        if (rights === 'admin' && !url.startsWith('/admin')) {
          this.router.navigate(['/admin']);
          return false;
        }
        if (rights === 'base' && url.startsWith('/admin')) {
          this.router.navigate(['/dashboard']);
          return false;
        }
        return true;
      }),
      catchError(err => {
        localStorage.removeItem('userData');
        if (url.startsWith('/auth')) {
          return of(true);
        }
        this.router.navigate(['/auth/login']);
        return of(false);
      })
    );
  }
}
