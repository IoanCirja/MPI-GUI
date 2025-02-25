import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
    const userData: any = JSON.parse(localStorage.getItem('userData') ?? '{}'); 
    request = request.clone({
        setHeaders: {
            Authorization: userData?.token ? `Bearer ${userData.token}` : '',
        }
    });

    return next(request);
};
