import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FileUploadService } from '../services/upload.service';
import { DashboardService } from '../services/dashboard.service';
import { CommonModule } from '@angular/common';
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ChartType } from 'chart.js';
import { UserQuota } from '../models/UserQuota';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  imports: [CommonModule, NgChartsModule],
})
export class DashboardComponent implements OnInit {
  jobData: any[] = [];

  statusChartData!: ChartConfiguration<'bar'>['data'];
  statusChartType: ChartType = 'bar';

  processesChartData!: ChartConfiguration<'bar'>['data'];
  processesChartType: ChartType = 'bar';

  durationChartData!: ChartConfiguration<'line'>['data'];
  durationChartType: ChartType = 'line';
  objectKeys = Object.keys;

  chartOptions: ChartOptions = {
    responsive: true,
    plugins: {
      legend: { display: true },
    },
    scales: {
      x: {},
      y: { beginAtZero: true },
    },
  };

  userQuota: UserQuota | null = null;

  constructor(
    private fileUploadService: FileUploadService,
    private dashboardService: DashboardService,
    private cdRef: ChangeDetectorRef
  ) {}

  async ngOnInit(): Promise<void> {
    await this.getJobStatus();
    await this.getQuota();
    this.generateCharts();
  }

  getJobStatus(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.fileUploadService.getJobStatus().subscribe({
        next: (response: any) => {
          this.jobData = [...response];
          this.cdRef.detectChanges();
          resolve();
        },
        error: (error) => {
          reject(error);
        },
      });
    });
  }

  getQuota(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.dashboardService.getUserQuota().subscribe({
        next: (quota) => {
          this.userQuota = quota;
          this.cdRef.detectChanges();
          resolve();
        },
        error: (error) => {
          reject(error);
        },
      });
    });
  }

  generateCharts() {
    this.generateStatusChart();
    this.generateProcessesChart();
    this.generateDurationChart();
  }

  generateStatusChart() {
    const statusCount: { [key: string]: number } = {};
    for (const job of this.jobData) {
      statusCount[job.status] = (statusCount[job.status] || 0) + 1;
    }

    this.statusChartData = {
      labels: Object.keys(statusCount),
      datasets: [
        {
          data: Object.values(statusCount),
          label: 'Jobs by Status',
          backgroundColor: 'rgba(75,192,192,0.6)',
        },
      ],
    };
  }

  generateProcessesChart() {
    this.processesChartData = {
      labels: this.jobData.map((job) => job.jobName),
      datasets: [
        {
          data: this.jobData.map((job) => job.numProcesses),
          label: 'Processes per Job',
          backgroundColor: 'rgba(153,102,255,0.6)',
        },
      ],
    };
  }

  generateDurationChart() {
    this.durationChartData = {
      labels: this.jobData.map((job) => job.jobName),
      datasets: [
        {
          data: this.jobData.map((job) => {
            const start = new Date(job.beginDate).getTime();
            const end = new Date(job.endDate).getTime();
            return (end - start) / 1000;
          }),
          label: 'Job Duration (s)',
          fill: false,
          borderColor: '#42A5F5',
          tension: 0.3,
        },
      ],
    };
  }
}
