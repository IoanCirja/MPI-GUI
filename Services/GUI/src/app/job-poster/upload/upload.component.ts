import { Component } from '@angular/core';
import { FileUploadService } from './upload.service';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HeaderComponent } from '../../header/header.component';
import { MatTooltipModule } from '@angular/material/tooltip';

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
})
export class UploadComponent {
  selectedFile: File | null = null;
  uploadMessage: string = '';
  numProcesses: number | null = null;
  executionOutput: string = '';
  isLoading: boolean = false;
  allowOverSubscription: boolean = false;
  jobName: string = '';
  jobDescription: string = '';
  lastExecutionTime: Date = new Date();
  isValidFile: boolean = false;

  nodeList: string[] = Array.from(
    { length: 21 },
    (_, i) => `C05-${i.toString().padStart(2, '0')}`
  );
  selectedNodes: boolean[] = new Array(21).fill(false);
  slots: number[] = new Array(21).fill(10);
  isDropdownVisible: boolean = false;

  constructor(
    private fileUploadService: FileUploadService,
    private router: Router
  ) {}

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
      this.selectedNodesList.push(this.nodeList[index]);
      this.slots.push(1);
    } else {
      const nodeIndex = this.selectedNodesList.indexOf(this.nodeList[index]);
      if (nodeIndex > -1) {
        this.selectedNodesList.splice(nodeIndex, 1);
        this.slots.splice(nodeIndex, 1);
      }
    }
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
      this.uploadMessage =
        'Please select a file and provide the number of processes!';
      return;
    }

    const hostfile = this.generateHostfile();
    this.router.navigate(['jobs/status']);

    this.isLoading = true;
    console.log('Uploading file with numProcesses:', this.numProcesses);
    console.log('Allow over subscription:', this.allowOverSubscription);
    this.lastExecutionTime = new Date();
    this.fileUploadService
      .uploadFile(
        this.selectedFile,
        this.numProcesses!,
        this.allowOverSubscription,
        hostfile,
        this.jobName,
        this.jobDescription,
        this.lastExecutionTime.toISOString()
      )
      .subscribe({
        next: (response: any) => {
          this.uploadMessage = response.message;
          this.executionOutput =
            response.execution_output || 'No output from the command';
          this.isLoading = false;
        },
        error: (error) => {
          console.log('Error:', error);
          this.uploadMessage = `Failed to upload file: ${
            error.error.message || 'Unknown error'
          }`;
          this.executionOutput =
            error.error.detail || 'No output from the command';
          this.isLoading = false;
        },
      });
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

  previewCommand() {}
}
