import { Component } from '@angular/core';
import { FileUploadService } from './upload.service';
import virustotal from '@api/virustotal';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
export class UploadComponent {
  selectedFile: File | null = null;
  uploadMessage: string = '';
  numProcesses: number | null = null;
  executionOutput: string = ''; 
  isLoading: boolean = false; 
  virusTotalStatus: string = ''; 

  constructor(private fileUploadService: FileUploadService) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length > 0) {
      const file = input.files[0];

      
      if (file.name.endsWith('.exe') || file.name.endsWith('.cpp')) {
        this.selectedFile = file;
        this.uploadMessage = `Selected file: ${file.name}`;
      } else {
        this.selectedFile = null;
        this.uploadMessage = 'Only .exe or .cpp files are allowed!';
      }
    }
  }

  
  uploadFile(): void {
    if (!this.selectedFile || !this.numProcesses) {
      this.uploadMessage = 'Please select a file and provide the number of processes!';
      return;
    }

    
    this.isLoading = true;
    console.log('Uploading file with numProcesses:', this.numProcesses); 

    
    this.fileUploadService.uploadFile(this.selectedFile, this.numProcesses!).subscribe({
      next: (response: any) => {
        this.uploadMessage = response.message;
        this.executionOutput = response.execution_output || 'No output from the command'; 
        this.isLoading = false; 
      },
      error: (error) => {
        this.uploadMessage = `Failed to upload file: ${error.error.message || 'Unknown error'}`;
        this.executionOutput = ''; 
        this.isLoading = false; 
      }
    });
  }
}
