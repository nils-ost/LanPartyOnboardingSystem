import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from '@angular/core';
import { ConfirmationService } from 'primeng/api';
import { Device } from 'src/app/interfaces/device';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Participant } from 'src/app/interfaces/participant';
import { Port } from 'src/app/interfaces/port';
import { Seat } from 'src/app/interfaces/seat';
import { Switch } from 'src/app/interfaces/switch';
import { Table } from 'src/app/interfaces/table';
import { Vlan } from 'src/app/interfaces/vlan';
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
  @Input() vlans: Vlan[] = [];
  @Output() editedDeviceEvent = new EventEmitter<null>();

  @ViewChild('editdesc') editDescDialog: any;
  @ViewChild('editseat') editSeatDialog: any;

  currentTs: number = 0;
  seatsOptions: any[] = [];
  seatsReadable: Map<string, string> = new Map<string, string>;
  ippoolsReadable: Map<string, string> = new Map<string, string>;
  participantsReadable: Map<string, string> = new Map<string, string>;
  portsReadable: Map<string, string> = new Map<string, string>;
  devicesReadable: Map<string, string> = new Map<string, string>;

  newSeatId: string | null = null;
  selectedDevice: Device | undefined = undefined;
  selectedDeviceName: string = "";
  newDesc: string = "";
  editVlanConfigDialog: boolean = false;

  constructor(
    public utils: UtilsService,
    private errorHandler: ErrorHandlerService,
    private confirmationService: ConfirmationService,
    private deviceService: DeviceService
  ) {
    this.currentTs = Math.floor(Date.now() / 1000);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (('tables' in changes || 'seats' in changes) && this.tables.length > 0 && this.seats.length > 0) {
      let tablesById: Map<string, Table> = new Map<string, Table>;
      let newList: any[] = [];
      newList.push({name: '--null--', code: null});
      for (let i = 0; i < this.tables.length; i++) tablesById.set(this.tables[i].id, this.tables[i]);
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        let table: Table | undefined = tablesById.get(seat.table_id);
        if (table) {
          let name: string = table.number + '(' + table.desc + ')' + ': #' + seat.number;
          this.seatsReadable.set(seat.id, name);
          newList.push({name: name, code: seat.id});
        }
      }
      this.seatsOptions = newList;
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

    if ('devices' in changes) {
      for (let i = 0; i < this.devices.length; i++) {
        let device: Device = this.devices[i];
        this.devicesReadable.set(device.id, device.mac + ' (' + device.desc + ')');
      }
      this.currentTs = Math.floor(Date.now() / 1000);
    }

    if (('switches' in changes || 'ports' in changes) && this.switches.length > 0 && this.ports.length > 0) {
      let switchesById: Map<string, Switch> = new Map<string, Switch>;
      for (let i = 0; i < this.switches.length; i++) switchesById.set(this.switches[i].id, this.switches[i]);
      for (let i = 0; i < this.ports.length; i++) {
        let port: Port = this.ports[i];
        let swi: Switch | undefined = switchesById.get(port.switch_id);
        if (swi) this.portsReadable.set(port.id, swi.desc + ': #' + port.number_display);
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

  editSeatStart(device: Device, event: any) {
    this.selectedDevice = device;
    this.newSeatId = device.seat_id;
    this.editSeatDialog.show(event);
  }

  deleteDevice(device: Device) {
    this.deviceService
      .deleteDevice(device.id)
      .subscribe({
        next: (response: any) => {
          this.editedDeviceEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  editSeatCheck() {
    if (this.selectedDevice) {
      if (this.newSeatId) {
        let havingDevice: Device | undefined = undefined;
        for (let i = 0; i < this.devices.length; i++) {
          if (this.devices[i].seat_id == this.newSeatId) {
            havingDevice = this.devices[i];
            break;
          }
        }
        if (havingDevice) {
          if (havingDevice.id != this.selectedDevice.id) {
            this.confirmationService.confirm({
              message: 'Seat "' + this.seatsReadable.get(this.newSeatId) + '" is allready assigned to Device "' + this.devicesReadable.get(havingDevice.id) + '". Are you sure to assign it to Device "' + this.devicesReadable.get(this.selectedDevice.id) + '"?',
              accept: () => {
                this.editSeat(havingDevice!.id);
              }
            });
          }
          else {
            // Nothing needs to be done as device is allready having this seat (close dialog)
            this.selectedDevice = undefined;
            this.editSeatDialog.hide();
          }
        }
        else this.editSeat(undefined);
      }
      else this.editSeat(undefined);
    }
  }

  editSeat(havingDevice_id: string | undefined) {
    if (this.selectedDevice) {
      if (havingDevice_id) {
        this.deviceService
          .removeSeat(havingDevice_id)
          .subscribe({
            next: (response: any) => {
              this.editSeat(undefined);
            },
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
      else {
        if (this.newSeatId) {
          this.deviceService
            .updateSeatId(this.selectedDevice.id, this.newSeatId)
            .subscribe({
              next: (response: any) => {
                this.editedDeviceEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
              }
            })
        }
        else {
          this.deviceService
            .removeSeat(this.selectedDevice.id)
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
      this.editSeatDialog.hide();
    }
  }

  removePort(device: Device) {
    this.deviceService
      .removePort(device.id)
      .subscribe({
        next: (response: any) => {
          this.editedDeviceEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  editVlanConfigStart(device: Device, event: any) {
    this.selectedDevice = device;
    this.selectedDeviceName = this.selectedDevice.desc + " (" + device.mac + ")"
    this.editVlanConfigDialog = true;
  }

  editVlanConfigAbort() {
    this.selectedDevice = undefined;
    this.selectedDeviceName = "";
    this.editVlanConfigDialog = false;
  }

  editVlanConfigEnd() {
    this.selectedDevice = undefined;
    this.selectedDeviceName = "";
    this.editedDeviceEvent.emit();
    this.editVlanConfigDialog = false;
  }
}
