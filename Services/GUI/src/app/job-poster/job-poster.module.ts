import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { FormsModule } from '@angular/forms';  
import { JobStatusComponent } from './job-status/job-status.component';

const routes: Routes = [
  { path: 'upload-job', component: UploadComponent },
  { path: 'status', component: JobStatusComponent },
];

@NgModule({
  declarations: [UploadComponent, JobStatusComponent],  
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    FormsModule,  
  ],
  exports: [RouterModule]
})
export class JobPosterModule { }
