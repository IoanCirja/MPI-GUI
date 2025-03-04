import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import {
  trigger,
  transition,
  style,
  animate,
  query,
} from '@angular/animations';
import { FileUploadService } from '../upload/upload.service';
import { WebSocketService } from './websocket.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-job-status',
  templateUrl: './job-status.component.html',
  styleUrls: ['./job-status.component.css'],
  imports: [CommonModule],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms 100ms', style({ opacity: 1 })),
      ]),
    ]),
  ],
})
export class JobStatusComponent implements OnInit {

  jobData: any[] = [];
  expandedJobs: Set<number> = new Set();
  loading: boolean = true;

  constructor(
    private fileUploadService: FileUploadService,
    private webSocketService: WebSocketService,
    private cdRef: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  async ngOnInit(): Promise<void> {
    await this.getJobStatus();
    this.listenToWebSocketUpdates();
  }

  getJobStatus(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.fileUploadService.getJobStatus().subscribe({
        next: (response: any) => {
          this.jobData = [...response];
          console.log('Fetched job data:', this.jobData);
          this.loading = false;
          this.cdRef.detectChanges();
          resolve();
        },
        error: (error) => {
          console.error('Error fetching job data:', error);
          reject(error);
        },
      });
    });
  }

  toggleExpand(jobIndex: number): void {
    if (this.expandedJobs.has(jobIndex)) {
      this.expandedJobs.delete(jobIndex);
    } else {
      this.expandedJobs.add(jobIndex);
    }
  }

  decodeBase64(encodedString: string): string {
    try {
      return atob(encodedString);
    } catch (e) {
      console.error('Failed to decode Base64:', e);
      return encodedString;
    }
  }

  listenToWebSocketUpdates(): void {
    this.webSocketService.connect().subscribe((update: any) => {
      console.log('WebSocket update received:', update);

      this.ngZone.run(() => {
        const index = this.jobData.findIndex(
          (job) => String(job.id) === String(update.jobId)
        );

        if (index !== -1) {
          this.jobData[index] = {
            ...this.jobData[index],
            status: update.status,
            output: update.output,
            endDate: update.endDate,
            isLoading: update.status === 'pending',
          };
        }

        console.log('Updated job data:', this.jobData);

        this.jobData = [...this.jobData];
        this.cdRef.detectChanges();
      });
    });
  }

  killJob(jobId: string): void {

    this.fileUploadService.killJob(jobId).subscribe({
      next: (response) => {
        console.log('Job kill request sent:', response);
      },
      error: (error) => {
        console.error('Error killing job:', error);
      },
    });
  }
  
}
