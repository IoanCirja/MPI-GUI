import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { FormsModule } from '@angular/forms';  

const routes: Routes = [
  { path: 'upload-job', component: UploadComponent },
];

@NgModule({
  declarations: [UploadComponent],  
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    FormsModule,  
  ],
  exports: [RouterModule]
})
export class JobPosterModule { }
