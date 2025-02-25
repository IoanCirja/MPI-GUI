import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app.routes';  
import { MatToolbarModule } from '@angular/material/toolbar';  
import { HeaderComponent } from './header/header.component';

@NgModule({
  imports: [
    BrowserModule,
    BrowserAnimationsModule,  
    AppRoutingModule,         
    MatToolbarModule,
    AppComponent,
    HeaderComponent,
    AppRoutingModule          
  ],
  providers: [],
})
export class AppModule { }
