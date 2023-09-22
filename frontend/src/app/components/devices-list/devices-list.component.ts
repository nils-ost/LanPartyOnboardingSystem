import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Device } from 'src/app/interfaces/device';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'app-devices-list',
  templateUrl: './devices-list.component.html',
  styleUrls: ['./devices-list.component.scss']
})
export class DevicesListComponent {
  @Input() devices: Device[] = [];
  @Output() editedDeviceEvent = new EventEmitter<null>();

  constructor(
    public utils: UtilsService
  ) {}
}
