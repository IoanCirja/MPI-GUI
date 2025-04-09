import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FileUploadService } from '../services/upload.service';
import { CommonModule } from '@angular/common';
import { NgxChartsModule } from '@swimlane/ngx-charts';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  imports: [CommonModule, NgxChartsModule],
})
export class DashboardComponent implements OnInit {
  jobData: any[] = [];
  chartData: any[] = [];
  view: [number, number] = [1000, 600];

  // Chart options
  legend = true;
  showXAxis = true;
  showYAxis = true;
  showGridLines = true;
  autoScale = false; // Disable auto-scaling to keep all nodes visible
  roundDomains = false;
  curveType = 'linear'; // Can be 'step', 'monotoneX', etc.

  // Define fixed node list for Y-axis
  nodesList: string[] = Array.from({ length: 21 }, (_, i) => `C${String(i).padStart(2, '0')}`);

  // Y-axis formatting function
  yAxisTickFormatting: any;
  xAxisTickFormatting: any;
  constructor(private fileUploadService: FileUploadService, private cdRef: ChangeDetectorRef) {
    // Formatting function for dates on the X-axis
    this.xAxisTickFormatting = (date: Date) => {
      return new Intl.DateTimeFormat('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date(date));
    };

    // Formatting function for Y-axis to display nodes correctly
    this.yAxisTickFormatting = (value: number) => {
      return this.nodesList[value] || '';
    };
  }

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
    const groupedData: { name: string; series: any[] }[] = [];

    // Ensure all nodes are always included
    this.nodesList.forEach(node => {
      groupedData.push({
        name: node,
        series: [] // Start with an empty series
      });
    });

    this.jobData.forEach(job => {
      const decodedHostfile = this.decodeBase64(job.hostFile);
      const usedNodes = this.extractNodes(decodedHostfile);
      const jobDate = new Date(job.beginDate);

      usedNodes.forEach(node => {
        let nodeData = groupedData.find(d => d.name === node);
        if (!nodeData) {
          nodeData = { name: node, series: [] };
          groupedData.push(nodeData);
        }

        nodeData.series.push({
          name: jobDate.toISOString(), // X-axis (Date as ISO string)
          value: this.nodesList.indexOf(node), // Y-axis (Node index)
          extra: { ...job } // Full job details for tooltip
        });
      });
    });

    this.chartData = groupedData;
    console.log('Transformed chart data:', this.chartData);
  }

  decodeBase64(encodedString: string): string {
    try {
      return atob(encodedString);
    } catch (e) {
      console.error('Failed to decode Base64:', e);
      return encodedString;
    }
  }

  extractNodes(hostfileContent: string): string[] {
    const nodeRegex = /C\d{2}-\d{2}/g;
    const matches = hostfileContent.match(nodeRegex);
    return matches ? Array.from(new Set(matches)) : [];
  }

  onSelect(event: any): void {
    console.log('Job data on hover:', event.extra);
  }
}
