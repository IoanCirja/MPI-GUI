import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FileUploadService } from '../upload/upload.service';
import { WebSocketService } from './websocket.service';

@Component({
  selector: 'app-job-status',
  templateUrl: './job-status.component.html',
  styleUrls: ['./job-status.component.css']
})
export class JobStatusComponent implements OnInit {
  jobData: any[] = [];
  expandedJobs: Set<number> = new Set();

  constructor(
    private fileUploadService: FileUploadService,
    private webSocketService: WebSocketService,
    private cdRef: ChangeDetectorRef  
  ) {}

  ngOnInit(): void {
    this.getJobStatus();
    this.listenToWebSocketUpdates();
  }

  getJobStatus(): void {
    this.fileUploadService.getJobStatus().subscribe({
      next: (response: any) => {
        this.jobData = response;
        console.log('Fetched job data:', this.jobData);
      },
      error: (error) => {
        console.error('Error fetching job data:', error);
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

  listenToWebSocketUpdates(): void {
    this.webSocketService.connect().subscribe((update: any) => {
      console.log('WebSocket update:', update);
  
      const updatedJobData = this.jobData.map(job => {
        if (job.id === update.jobId) {
          return {
            ...job,
            status: update.status,
            output: update.output,
            isLoading: update.status === 'pending' ? true : false
          };
        }
        return job;
      });
  
      this.jobData = updatedJobData;
  
      this.cdRef.detectChanges();
    });
  }
  
}
