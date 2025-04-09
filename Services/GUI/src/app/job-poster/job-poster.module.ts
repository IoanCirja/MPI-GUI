import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { FormsModule } from '@angular/forms';  
import { JobStatusComponent } from './job-status/job-status.component';
import { FileUploadService } from '../services/upload.service';
import { AuthGuard } from '../auth.guard';  

const routes: Routes = [
  { path: 'upload-job', component: UploadComponent, canActivate: [AuthGuard] },  
  { path: 'status', component: JobStatusComponent, canActivate: [AuthGuard] },   
];

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    FormsModule,
    UploadComponent,
    JobStatusComponent,
  ],
  providers: [FileUploadService],
  exports: [RouterModule]
})
export class JobPosterModule { }
