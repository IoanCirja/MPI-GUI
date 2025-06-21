import { Component, OnDestroy, OnInit } from '@angular/core';
import { FileUploadService } from '../../services/upload.service';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HeaderComponent } from '../../header/header.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { animate, style, transition, trigger } from '@angular/animations';
import { Job } from '../models/Job';
import { WebSocketService } from './websocket.service';

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
  slots: number[] = new Array(21).fill(10);
  isDropdownVisible: boolean = false;
  environmentVars: string = '';
  displayMap: boolean = false;
  rankBy: any;
  mapBy: any;
  availableNodes: boolean[] = new Array(21).fill(false); 
  errorMessage: string = '';  



  constructor(
    private fileUploadService: FileUploadService,
    private router: Router,
    private webSocketService: WebSocketService,
    
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
        
        
        this.availableNodes = this.nodeList.map((node) => update[node] || false);

        console.log('Available nodes:', this.availableNodes);
        console.log('Selected nodes:', update);
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

      if (file.name.endsWith('.exe') || file.name.endsWith('.cpp')) {
        this.selectedFile = file;
        this.uploadMessage = `Selected file: ${file.name}`;
        this.isValidFile = true;
      } else {
        this.selectedFile = null;
        this.isValidFile = false;
        this.uploadMessage = 'Only .exe or .cpp files are allowed!';
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

      if (file.name.endsWith('.exe') || file.name.endsWith('.cpp')) {
        this.selectedFile = file;
        this.uploadMessage = `Selected file: ${file.name}`;
        this.isValidFile = true;
      } else {
        this.selectedFile = null;
        this.isValidFile = false;
        this.uploadMessage = 'Only .exe or .cpp files are allowed!';
      }
    }
  }

  showNodeDropdown: boolean = false;

  selectedNodesList: string[] = [];

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
    const selectedNodesWithSlots = this.nodeList
      .filter((node, index) => this.selectedNodes[index])
      .map((node, index) => ({
        node,
        slots: this.slots[index],
      }));

    let hostfileContent = '';

    selectedNodesWithSlots.forEach(({ node, slots }) => {
      hostfileContent += `${node} slots=${slots}\n`;
    });

    console.log('Hostfile content:', hostfileContent);

    const blob = new Blob([hostfileContent], { type: 'text/plain' });

    return new File([blob], 'hostfile', { type: 'text/plain' });
  }

  uploadFile(): void {
    if (!this.selectedFile || !this.numProcesses) {
      this.uploadMessage = 'Please select a file and provide the number of processes!';
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
          allowOverSubscription: this.allowOverSubscription,
          environmentVars: this.environmentVars,
          displayMap: this.displayMap,
          rankBy: this.rankBy,
          mapBy: this.mapBy,
          status: 'pending',
          output: '',
          alertOnFinish: this.alertOnFinish,
        };
        console.log('Uploading job:', job);
        this.isLoading = true;
  
        this.fileUploadService.uploadFile(job).subscribe({
          next: (response: any) => {
            this.uploadMessage = response.message;
            this.executionOutput = response.execution_output || 'No output from the command';
            this.isLoading = false;
            this.router.navigate(['jobs/status']);
          },
          error: (error) => {
            console.log('Error:', error);
            this.uploadMessage = `Failed to upload file: ${error.error.message || 'Unknown error'}`;
            this.executionOutput = error.error.detail || 'No output from the command';
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
    this.numProcesses = 1;
    this.allowOverSubscription = false;
    this.selectedNodes = [];
    this.slots = [];
    this.executionOutput = '';
    this.uploadMessage = '';

  }

  saveJobData(): void {
    const jobData = {
      jobName: this.jobName,
      jobDescription: this.jobDescription,
      startDate: this.startDate,
      endDate: this.endDate,
      allowOverSubscription: this.allowOverSubscription,
      environmentVars: this.environmentVars,
      displayMap: this.displayMap,
      rankBy: this.rankBy,
      mapBy: this.mapBy,
      selectedFile: this.selectedFile ? this.selectedFile.name : null,
      selectedNodes: this.nodeList.filter((_, index) => this.selectedNodes[index]),
      slots: this.selectedNodes.map((selected, index) => selected ? this.slots[index] : 0),
      numProcesses: this.numProcesses,
    };

    
    const jsonData = JSON.stringify(jobData, null, 2); 

    
    const blob = new Blob([jsonData], { type: 'application/json' });

    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${this.jobName || 'job'}_data.json`; 
    link.click();
  }

  
}


