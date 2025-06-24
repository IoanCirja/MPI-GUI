import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket!: WebSocket;
  private messages: Subject<any> = new Subject();

  connect(): Observable<any> {
    this.socket = new WebSocket('ws://localhost:8002/api/ws');

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('WebSocket message:', message);
      this.messages.next(message);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = () => {
      console.warn('WebSocket connection closed');
    };

    

    return this.messages.asObservable();
  }


}
