import { Component, OnDestroy, OnInit } from '@angular/core';
import { FileUploadService } from '../../services/upload.service';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HeaderComponent } from '../../header/header.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { animate, style, transition, trigger } from '@angular/animations';
import { Job } from '../../models/Job';
import { WebNodesSocketService } from '../../services/websocketnode.service';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  imports: [
    FormsModule,
    CommonModule,
    MatIconModule,
    HeaderComponent,
    MatTooltipModule,
  ],
  styleUrls: ['./upload.component.css'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms 100ms', style({ opacity: 1 })),
      ]),
    ]),
  ],
})
export class UploadComponent implements OnInit, OnDestroy {
  selectedFile: File | null = null;
  uploadMessage: string = '';
  numProcesses: number | null = null;
  executionOutput: string = '';
  isLoading: boolean = false;
  allowOverSubscription: boolean = false;
  jobName: string = '';
  jobDescription: string = '';
  endDate: string = '';
  startDate: string = '';
  isValidFile: boolean = false;
  alertOnFinish: boolean = false;

  nodeList: string[] = Array.from(
    { length: 21 },
    (_, i) => `C05-${i.toString().padStart(2, '0')}`
  );

  selectedNodes: boolean[] = new Array(21).fill(false);
  slots: number[] = new Array(21).fill(0);
  isDropdownVisible: boolean = false;
  environmentVars: string = '';
  displayMap: boolean = false;
  rankBy: any;
  mapBy: any;
  availableNodes: boolean[] = new Array(21).fill(false);
  errorMessage: string = '';
  showNodeDropdown: boolean = false;
  selectedNodesList: string[] = [];


  environmentVarsValid: boolean = true;
  jobNameValid = true;
  jobDescriptionValid = true;
  private safeTextPattern = /^[^;&|$`<>]+$/;
  validateJobName(): void {
    this.jobNameValid = this.safeTextPattern.test(this.jobName.trim());
  }

  validateJobDescription(): void {
    this.jobDescriptionValid = this.safeTextPattern.test(this.jobDescription.trim());
  }

  validateEnvVars(): void {
    if (!this.environmentVars) {
      this.environmentVarsValid = true;
      return;
    }
    const parts = this.environmentVars.split(',');
    const pattern = /^[A-Za-z_][A-Za-z0-9_]*=[^;&|$()<>`]+$/;
    this.environmentVarsValid = parts.every(p => pattern.test(p.trim()));
  }

  constructor(
    private fileUploadService: FileUploadService,
    private router: Router,
    private webSocketService: WebNodesSocketService
  ) {}

  ngOnInit(): void {
    this.listenToWebSocketUpdates();
  }

  ngOnDestroy(): void {
    this.webSocketService.disconnect();
  }

  listenToWebSocketUpdates(): void {
    this.webSocketService.connect().subscribe(
      (update: any) => {
        console.log('WebSocket update received:', update);

        this.availableNodes = this.nodeList.map(
          (node) => update[node] || false
        );

        console.log('Available nodes:', this.availableNodes);
      },
      (error) => {
        console.error('WebSocket error:', error);
      }
    );
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length > 0) {
      const file = input.files[0];

      if (file.name.endsWith('.exe')) {
        this.selectedFile = file;
        this.uploadMessage = `Selected file: ${file.name}`;
        this.isValidFile = true;
      } else {
        this.selectedFile = null;
        this.isValidFile = false;
        this.uploadMessage = 'Only .exe files are allowed!';
      }
    }
  }

  toggleNodeDropdown() {
    this.isDropdownVisible = !this.isDropdownVisible;
    this.updateNumProcesses();
  }
  triggerFileInput(): void {
    const fileInput = document.getElementById('fileInput') as HTMLInputElement;
    fileInput.click();
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    const dropzone = event.currentTarget as HTMLElement;
    dropzone.classList.add('drag-over');
  }

  onDragLeave(event: DragEvent): void {
    const dropzone = event.currentTarget as HTMLElement;
    dropzone.classList.remove('drag-over');
  }

  onFileDropped(event: DragEvent): void {
    event.preventDefault();
    const dropzone = event.currentTarget as HTMLElement;
    dropzone.classList.remove('drag-over');

    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];

      if (file.name.endsWith('.exe')) {
        this.selectedFile = file;
        this.uploadMessage = `Selected file: ${file.name}`;
        this.isValidFile = true;
      } else {
        this.selectedFile = null;
        this.isValidFile = false;
        this.uploadMessage = 'Only .exe files are allowed!';
      }
    }
  }

  toggleNodeSelection(index: number) {
    this.selectedNodes[index] = !this.selectedNodes[index];

    if (this.selectedNodes[index]) {
      if (!this.slots[index]) {
        this.slots[index] = 1;
      }
    } else {
      this.slots[index] = 0;
    }

    this.updateNumProcesses();
  }

  updateNumProcesses(): void {
    this.numProcesses = this.slots.reduce((sum, slot, index) => {
      return this.selectedNodes[index] ? sum + slot : sum;
    }, 0);
  }

  hasSelectedNodes(): boolean {
    return this.selectedNodes.some((selected) => selected);
  }
  
  clearSelectedFile(event: MouseEvent): void {
    event.stopPropagation();
    this.selectedFile = null;
    this.isValidFile = false;
    this.uploadMessage = '';
  }

  generateHostfile(): File {
    const lines = this.nodeList.reduce<string[]>((acc, node, i) => {
      if (this.selectedNodes[i]) {
        acc.push(`${node} slots=${this.slots[i]}`);
      }
      return acc;
    }, []);

    const blob = new Blob([lines.join("\n") + "\n"], { type: "text/plain" });
    return new File([blob], "hostfile.txt", { type: "text/plain" });
  }

  uploadFile(): void {
    if (!this.selectedFile || !this.numProcesses) {
      this.uploadMessage =
        'Please select a file and provide the number of processes!';
      return;
    }

    this.validateEnvVars();
    if (!this.environmentVarsValid) {
      this.errorMessage = 'Invalid environment variables format. Use VAR=value,VAR2=value2…';
      return;
    }

    this.validateJobName();
    if (!this.jobNameValid) {
      this.errorMessage = 'Job Name contains invalid characters.';
      return;
    }
    this.validateJobDescription();
    if (!this.jobDescriptionValid) {
      this.errorMessage = 'Job Description contains invalid characters.';
      return;
    }

    const reader = new FileReader();
    const hostFileReader = new FileReader();

    reader.onload = () => {
      hostFileReader.onload = () => {
        const job: Job = {
          jobName: this.jobName,
          jobDescription: this.jobDescription,
          beginDate: this.startDate,
          endDate: this.endDate,
          fileName: this.selectedFile!.name,
          fileContent: (reader.result as string).split(',')[1],
          hostFile: (hostFileReader.result as string).split(',')[1],
          hostNumber: this.selectedNodesList.length,
          numProcesses: this.numProcesses!,
          allowOverSubscription: this.allowOverSubscription ?? false,
          environmentVars: this.environmentVars ?? '',
          displayMap: this.displayMap ?? '',
          rankBy: this.rankBy ?? '',
          mapBy: this.mapBy ?? '',
          status: 'pending',
          output: '',
          alertOnFinish: this.alertOnFinish,
        };
        this.isLoading = true;

        this.fileUploadService.uploadFile(job).subscribe({
          next: (response: any) => {
            this.uploadMessage = response.message;
            this.executionOutput =
              response.execution_output || 'No output from the command';
            this.isLoading = false;
            this.router.navigate(['jobs/status']);
          },
          error: (error) => {
            console.log('Error:', error);
            this.uploadMessage = `Failed to upload file: ${
              error.error.message || 'Unknown error'
            }`;
            this.executionOutput =
              error.error.detail || 'No output from the command';
            this.isLoading = false;
            this.errorMessage = error.error.detail || 'Failed to upload file';
          },
        });
      };

      hostFileReader.readAsDataURL(this.generateHostfile());
    };

    reader.readAsDataURL(this.selectedFile);
  }

  cancelJob() {}

  clearForm() {
    this.jobName = '';
    this.jobDescription = '';
    this.selectedFile = null;
    this.numProcesses = 0;
    this.allowOverSubscription = false;
    this.selectedNodes = [];
    this.slots = [];
    this.executionOutput = '';
    this.uploadMessage = '';
    this.displayMap = false;
    this.alertOnFinish = false;
    this.environmentVars = '';
  }

saveJobData(): void {
  const cfg = {
    jobName: this.jobName,
    jobDescription: this.jobDescription,
    startDate: this.startDate,
    endDate: this.endDate,
    allowOverSubscription: this.allowOverSubscription,
    environmentVars: this.environmentVars,
    displayMap: this.displayMap,
    rankBy: this.rankBy,
    mapBy: this.mapBy,
    alertOnFinish: this.alertOnFinish,
    selectedNodes: this.selectedNodes,
    slots: this.slots,
    numProcesses: this.numProcesses,
  };
  const blob = new Blob([JSON.stringify(cfg, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${this.jobName || 'job'}_config.json`;
  a.click();
}

onLoadConfig(evt: Event): void {
  const input = evt.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    try {
      const cfg = JSON.parse(reader.result as string);

      this.jobName = cfg.jobName || '';
      this.jobDescription = cfg.jobDescription || '';
      this.startDate = cfg.startDate || '';
      this.endDate = cfg.endDate || '';
      this.allowOverSubscription = cfg.allowOverSubscription || false;
      this.environmentVars = cfg.environmentVars || '';
      this.displayMap = cfg.displayMap || false;
      this.rankBy = cfg.rankBy || '';
      this.mapBy = cfg.mapBy || '';
      this.alertOnFinish = cfg.alertOnFinish || false;

      this.selectedNodes = Array.isArray(cfg.selectedNodes)
        ? cfg.selectedNodes
        : new Array(this.nodeList.length).fill(false);
      this.slots = Array.isArray(cfg.slots)
        ? cfg.slots
        : new Array(this.nodeList.length).fill(0);

      this.numProcesses = cfg.numProcesses || 0;

      this.uploadMessage = 'Config loaded, please re-select your .exe file';
      this.errorMessage = '';
    } catch {
      this.errorMessage = 'invalid JSON';
    }
    input.value = '';
  };
  reader.readAsText(file);
}


}
