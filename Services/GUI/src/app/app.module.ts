import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';  // Import AppRoutingModule
import { MatToolbarModule } from '@angular/material/toolbar';  // Import Material Toolbar

@NgModule({
  declarations: [
    AppComponent  // Root component declaration
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,  // Required for Material animations
    AppRoutingModule,         // Import the routing module
    MatToolbarModule          // Import Angular Material's Toolbar
  ],
  providers: [],
  bootstrap: [AppComponent]  // Bootstrap the main AppComponent
})
export class AppModule { }
