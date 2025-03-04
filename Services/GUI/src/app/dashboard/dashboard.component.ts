import { Component, AfterViewInit } from '@angular/core';

declare var monaco: any;  // Monaco global object

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {

  constructor() {}



  initializeEditor() {
    monaco.editor.create(document.getElementById('container')!, {
      value: '#include <mpi.h>\nint main() {\n  MPI_Init(NULL, NULL);\n  MPI_Finalize();\n  return 0;\n}',
      language: 'cpp',
      theme: 'vs-dark',
      automaticLayout: true
    });
  }
}
