import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Device } from 'src/app/interfaces/device';
import { DeviceService } from 'src/app/services/device.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'app-devices-screen',
  templateUrl: './devices-screen.component.html',
  styleUrls: ['./devices-screen.component.scss']
})
export class DevicesScreenComponent implements OnInit {
  devices: Device[] = [];

  constructor(
    private errorHandler: ErrorHandlerService,
    private deviceService: DeviceService
  ) { }

  ngOnInit(): void {
    this.refreshDevices();
  }

  refreshDevices() {
    this.deviceService
      .getDevices()
      .subscribe({
        next: (devices: Device[]) => {
          this.devices = devices;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  creaditDevice() {
    this.refreshDevices();
  }
}
