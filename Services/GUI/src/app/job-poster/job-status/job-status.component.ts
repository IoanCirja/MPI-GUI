import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import {
  trigger,
  transition,
  style,
  animate,
  query,
} from '@angular/animations';
import { FileUploadService } from '../../services/upload.service';
import { WebSocketService } from '../../services/websocketstatus.service';
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
  nodeList: string[] = Array.from(
    { length: 21 },
    (_, i) => `C05-${i.toString().padStart(2, '0')}`
  );

  get hasRunningJobs(): boolean {
    return this.jobData.some((job) => job.status === 'running');
  }

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
          this.loading = false;
          this.cdRef.detectChanges();
          resolve();
        },
        error: (error) => {
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
      return encodedString;
    }
  }

  downloadExecutable(name: string, content: string): void {
    const decodedContent = this.decodeBase64(content);

    const blob = new Blob(
      [new Uint8Array(decodedContent.split('').map((c) => c.charCodeAt(0)))],
      { type: 'application/x-msdownload' }
    );

    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    link.click();
  }

  downloadHostfile(encodedHostfile: string): void {
    const decodedHostfile = this.decodeBase64(encodedHostfile);
    const blob = new Blob([decodedHostfile], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'hostfile.txt';
    link.click();
  }

  listenToWebSocketUpdates(): void {
    this.webSocketService.connect().subscribe((update: any) => {
      console.log('Wb update received:', update);

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
          };
        }

        this.jobData = [...this.jobData];
        this.cdRef.detectChanges();
      });
    });
  }

  killJob(jobId: string): void {
    this.fileUploadService.killJob(jobId).subscribe({
      next: (response) => {},
      error: (error) => {},
    });
  }

  deleteJob(jobId: string): void {
    const job = this.jobData.find((j) => j.id === jobId);
    if (job?.status === 'running') {
      return;
    }
    this.fileUploadService.deleteJob(jobId).subscribe({
      next: (response) => {
        this.jobData = this.jobData.filter((job) => job.id !== jobId);
      },
    });
  }

  clearHistory(): void {
    if (this.hasRunningJobs) {
      return;
    }
    this.fileUploadService.deleteJobs().subscribe({
      next: (response) => {
        this.jobData = [];
      },
    });
  }

  exportJob(jobId: string): void {
    const job = this.jobData.find((j) => j.id === jobId);
    if (!job) {
      return;
    }

    const decoded = this.decodeBase64(job.hostFile || '')
      .trim()
      .split('\n')
      .filter((l) => l);

    const selectedNodes = new Array(this.nodeList.length).fill(false);
    const slots = new Array(this.nodeList.length).fill(0);

    for (const line of decoded) {
      const [node, slotPart] = line.split(/\s+/);
      const idx = this.nodeList.indexOf(node);
      if (idx !== -1) {
        selectedNodes[idx] = true;
        const [, s] = slotPart.split('=');
        slots[idx] = parseInt(s, 10) || 0;
      }
    }

    const cfg = {
      jobName: job.jobName,
      jobDescription: job.jobDescription,
      startDate: job.beginDate,
      endDate: job.endDate,
      allowOverSubscription: job.allowOverSubscription,
      environmentVars: job.environmentVars,
      displayMap: job.displayMap,
      rankBy: job.rankBy,
      mapBy: job.mapBy,
      alertOnFinish: job.alertOnFinish,
      selectedNodes,
      slots,
      numProcesses: job.numProcesses,
    };

    const blob = new Blob([JSON.stringify(cfg, null, 2)], {
      type: 'application/json',
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${job.jobName || 'job'}_config.json`;
    a.click();
  }
}
