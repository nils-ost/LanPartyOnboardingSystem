import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { Device } from 'src/app/interfaces/device';
import { DeviceService } from 'src/app/services/device.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'app-devices-list',
  templateUrl: './devices-list.component.html',
  styleUrls: ['./devices-list.component.scss']
})
export class DevicesListComponent {
  @Input() devices: Device[] = [];
  @Output() editedDeviceEvent = new EventEmitter<null>();

  @ViewChild('editdesc') editDescDialog: any;

  selectedDevice: Device | undefined = undefined;
  newDesc: string = "";

  constructor(
    public utils: UtilsService,
    private errorHandler: ErrorHandlerService,
    private deviceService: DeviceService
  ) {}

  editDescStart(device: Device, event: any) {
    this.selectedDevice = device;
    this.newDesc = device.desc;
    this.editDescDialog.show(event);
  }

  editDesc() {
    this.editDescDialog.hide();
    if (this.selectedDevice) {
      this.deviceService
        .updateDesc(this.selectedDevice.id, this.newDesc)
        .subscribe({
          next: (response: any) => {
            this.editedDeviceEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedDevice = undefined;
  }

  setBlocked(device: Device, state: boolean) {
    this.deviceService
      .updateBlocked(device.id, state)
      .subscribe({
        next: (response: any) => {
          this.editedDeviceEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }
}
