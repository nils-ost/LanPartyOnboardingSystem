import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { Device } from 'src/app/interfaces/device';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Participant } from 'src/app/interfaces/participant';
import { Port } from 'src/app/interfaces/port';
import { Seat } from 'src/app/interfaces/seat';
import { Switch } from 'src/app/interfaces/switch';
import { System } from 'src/app/interfaces/system';
import { Table } from 'src/app/interfaces/table';
import { Vlan } from 'src/app/interfaces/vlan';
import { DeviceService } from 'src/app/services/device.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { ParticipantService } from 'src/app/services/participant.service';
import { PortService } from 'src/app/services/port.service';
import { SeatService } from 'src/app/services/seat.service';
import { SwitchService } from 'src/app/services/switch.service';
import { SystemService } from 'src/app/services/system.service';
import { TableService } from 'src/app/services/table.service';
import { VlanService } from 'src/app/services/vlan.service';

@Component({
  selector: 'app-devices-screen',
  templateUrl: './devices-screen.component.html',
  styleUrls: ['./devices-screen.component.scss']
})
export class DevicesScreenComponent implements OnInit {
  system!: System;
  devices: Device[] = [];
  tables: Table[] = [];
  seats: Seat[] = [];
  ippools: IpPool[] = [];
  participants: Participant[] = [];
  ports: Port[] = [];
  switches: Switch[] = [];
  vlans: Vlan[] = [];
  portFilter: string | null = null;

  constructor(
    private errorHandler: ErrorHandlerService,
    private deviceService: DeviceService,
    private tableService: TableService,
    private seatService: SeatService,
    private ippoolService: IpPoolService,
    private participantService: ParticipantService,
    private portService: PortService,
    private switchService: SwitchService,
    private vlanService: VlanService,
    private systemService: SystemService,
    private route: ActivatedRoute
  ) { }

  ngOnInit(): void {
    this.route.paramMap.subscribe({
      next: (params => {
        this.portFilter = params.get('port_id')
        this.refreshDevices();
      })
    })
    this.refreshSystem();
    this.refreshTables();
    this.refreshSeats();
    this.refreshIppools();
    this.refreshParticipants();
    this.refreshPorts();
    this.refreshSwitches();
    this.refreshVlans();
  }

  refreshSystem() {
    this.systemService
      .getSystem()
      .subscribe({
        next: (system: System) => {
          this.system = system;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshDevices() {
    this.deviceService
      .getDevices()
      .subscribe({
        next: (devices: Device[]) => {
          if (this.portFilter) {
            this.devices = [];
            for (let i = 0; i < devices.length; i++) {
              if (devices[i].port_id == this.portFilter) this.devices.push(devices[i]);
            }
          }
          else {
            this.devices = devices;
          }
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshTables() {
    this.tableService
      .getTables()
      .subscribe({
        next: (tables: Table[]) => {
          this.tables = tables;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshSeats() {
    this.seatService
      .getSeats()
      .subscribe({
        next: (seats: Seat[]) => {
          this.seats = seats;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshIppools() {
    this.ippoolService
      .getIpPools()
      .subscribe({
        next: (ippools: IpPool[]) => {
          this.ippools = ippools;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshParticipants() {
    this.participantService
      .getParticipants()
      .subscribe({
        next: (participants: Participant[]) => {
          this.participants = participants;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshPorts() {
    this.portService
      .getPorts()
      .subscribe({
        next: (ports: Port[]) => {
          this.ports = ports;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshSwitches() {
    this.switchService
      .getSwitches()
      .subscribe({
        next: (switches: Switch[]) => {
          this.switches = switches;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshVlans() {
    this.vlanService
      .getVlans()
      .subscribe({
        next: (vlans: Vlan[]) => {
          this.vlans = vlans;
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
