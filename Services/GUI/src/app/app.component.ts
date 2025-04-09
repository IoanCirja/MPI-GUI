import { ChangeDetectorRef, Component, effect, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './header/header.component';
import { UserService } from './services/user.service';
import { CommonModule } from '@angular/common';
import { animate, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HeaderComponent, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  

})
export class AppComponent implements OnInit {
  title = 'MPI Launcher';
  user: any = null;

  constructor(
    private userService: UserService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.userService.getProfile().subscribe(() => {});
    this.userService.getUser().subscribe((user) => {
      this.user = user;
      this.cdr.detectChanges();
    });
  }

}
