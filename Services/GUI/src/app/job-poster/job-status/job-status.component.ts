import { Component, OnInit } from '@angular/core';
import { FileUploadService } from '../upload/upload.service';

@Component({
  selector: 'app-job-status',
  templateUrl: './job-status.component.html',
  styleUrls: ['./job-status.component.css']
})
export class JobStatusComponent implements OnInit {
  jobData: any[] = [];  
  expandedJobs: Set<number> = new Set();  

  constructor(private fileUploadService: FileUploadService) {}

  ngOnInit(): void {
    this.getJobStatus();
  }

  
  getJobStatus(): void {
    this.fileUploadService.getJobStatus().subscribe({
      next: (response: any) => {
        this.jobData = response;  
        console.log('Fetched job data:', this.jobData);  
      },
      error: (error) => {
        console.error("Error fetching job data:", error);
      }
    });
  }

  
  toggleExpand(jobIndex: number): void {
    if (this.expandedJobs.has(jobIndex)) {
      this.expandedJobs.delete(jobIndex);  
    } else {
      this.expandedJobs.add(jobIndex);  
    }
  }

  
  downloadFile(base64String: string, fileName: string): void {
    const byteCharacters = atob(base64String);
    const byteNumbers = new Array(byteCharacters.length).fill(0).map((_, i) => byteCharacters.charCodeAt(i));
    const byteArray = new Uint8Array(byteNumbers);

    const blob = new Blob([byteArray]);
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();

    window.URL.revokeObjectURL(url);  
  }
}
