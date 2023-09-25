import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from '@angular/core';
import { Device } from 'src/app/interfaces/device';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Participant } from 'src/app/interfaces/participant';
import { Port } from 'src/app/interfaces/port';
import { Seat } from 'src/app/interfaces/seat';
import { Switch } from 'src/app/interfaces/switch';
import { Table } from 'src/app/interfaces/table';
import { DeviceService } from 'src/app/services/device.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'app-devices-list',
  templateUrl: './devices-list.component.html',
  styleUrls: ['./devices-list.component.scss']
})
export class DevicesListComponent implements OnChanges {
  @Input() devices: Device[] = [];
  @Input() tables: Table[] = [];
  @Input() seats: Seat[] = [];
  @Input() ippools: IpPool[] = [];
  @Input() participants: Participant[] = [];
  @Input() ports: Port[] = [];
  @Input() switches: Switch[] = [];
  @Output() editedDeviceEvent = new EventEmitter<null>();

  @ViewChild('editdesc') editDescDialog: any;

  seatsReadable: Map<string, string> = new Map<string, string>;
  ippoolsReadable: Map<string, string> = new Map<string, string>;
  participantsReadable: Map<string, string> = new Map<string, string>;
  portsReadable: Map<string, string> = new Map<string, string>;

  selectedDevice: Device | undefined = undefined;
  newDesc: string = "";

  constructor(
    public utils: UtilsService,
    private errorHandler: ErrorHandlerService,
    private deviceService: DeviceService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (('tables' in changes || 'seats' in changes) && this.tables.length > 0 && this.seats.length > 0) {
      let tablesById: Map<string, Table> = new Map<string, Table>;
      for (let i = 0; i < this.tables.length; i++) tablesById.set(this.tables[i].id, this.tables[i]);
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        let table: Table | undefined = tablesById.get(seat.table_id);
        if (table) this.seatsReadable.set(seat.id, table.number + '(' + table.desc + ')' + ': #' + seat.number);
      }
    }

    if ('ippools' in changes) {
      for (let i = 0; i < this.ippools.length; i++) {
        let ippool: IpPool = this.ippools[i];
        this.ippoolsReadable.set(ippool.id, ippool.desc);
      }
    }

    if ('participants' in changes) {
      for (let i = 0; i < this.participants.length; i++) {
        let participant: Participant = this.participants[i];
        let login: string = "";
        if (participant.login) login = participant.login;
        this.participantsReadable.set(participant.id, participant.name + ' (' + login + ')');
      }
    }

    if (('switches' in changes || 'ports' in changes) && this.switches.length > 0 && this.ports.length > 0) {
      let switchesById: Map<string, Switch> = new Map<string, Switch>;
      for (let i = 0; i < this.switches.length; i++) switchesById.set(this.switches[i].id, this.switches[i]);
      for (let i = 0; i < this.ports.length; i++) {
        let port: Port = this.ports[i];
        let swi: Switch | undefined = switchesById.get(port.switch_id);
        if (swi) this.portsReadable.set(port.id, swi.desc + ': #' + port.number);
      }
    }
  }

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
