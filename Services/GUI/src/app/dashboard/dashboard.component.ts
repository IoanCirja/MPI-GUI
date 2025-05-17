import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FileUploadService } from '../services/upload.service';
import { CommonModule } from '@angular/common';
import { NgChartsModule } from 'ng2-charts';  // Chart.js module
import { ChartConfiguration, ChartOptions } from 'chart.js';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  imports: [CommonModule, NgChartsModule], // Use NgChartsModule
})
export class DashboardComponent implements OnInit {
  jobData: any[] = [];
  chartLabels: string[] = [];
  chartData: { data: number[]; label: string }[] = [];

  chartOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: { display: true },
    },
    scales: {
      x: { title: { display: true, text: 'Begin Date' } },
      y: { title: { display: true, text: 'Number of Processes' } }
    }
  };

  constructor(private fileUploadService: FileUploadService, private cdRef: ChangeDetectorRef) {}

  async ngOnInit(): Promise<void> {
    await this.getJobStatus();
  }

  getJobStatus(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.fileUploadService.getJobStatus().subscribe({
        next: (response: any) => {
          this.jobData = [...response];
          console.log('Fetched job data:', this.jobData);
          this.transformData();
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

  transformData(): void {
    this.chartLabels = this.jobData.map(job => job.beginDate);
    const processes = this.jobData.map(job => job.numProcesses);

    this.chartData = [
      { data: processes, label: 'Number of Processes' }
    ];
  }
}
