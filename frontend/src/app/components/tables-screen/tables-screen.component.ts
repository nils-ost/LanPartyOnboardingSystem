import { Component, OnInit, ViewChild } from '@angular/core';
import { ErrorHandlerService } from '../../services/error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { Vlan } from '../../interfaces/vlan';
import { VlanService } from '../../services/vlan.service';
import { Switch } from 'src/app/interfaces/switch';
import { SwitchService } from 'src/app/services/switch.service';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { Table } from 'src/app/interfaces/table';
import { TableService } from 'src/app/services/table.service';
import { Seat } from 'src/app/interfaces/seat';
import { SeatService } from 'src/app/services/seat.service';
import { Participant } from 'src/app/interfaces/participant';
import { ParticipantService } from 'src/app/services/participant.service';
import { SystemService } from 'src/app/services/system.service';
import { System } from 'src/app/interfaces/system';

@Component({
  selector: 'app-tables-screen',
  templateUrl: './tables-screen.component.html',
  styleUrls: ['./tables-screen.component.scss']
})
export class TablesScreenComponent implements OnInit {
  @ViewChild('createtable') createTableDialog: any;
  system!: System;
  vlans: Vlan[] = [];
  switches: Switch[] = [];
  ippools: IpPool[] = [];
  tables: Table[] = [];
  seats: Seat[] = [];
  participants: Participant[] = [];

  selectedTable: Table | undefined;
  absolute_seatnumbers: boolean = false;

  constructor(
    private errorHandler: ErrorHandlerService,
    private systemService: SystemService,
    private vlanService: VlanService,
    private switchService: SwitchService,
    private ippoolService: IpPoolService,
    private tableService: TableService,
    private seatService: SeatService,
    private participantService: ParticipantService
  ) { }

  ngOnInit(): void {
    this.refreshSystem();
    this.refreshVlans();
    this.refreshSwitches();
    this.refreshIpPools();
    this.refreshTables();
    this.refreshSeats();
    this.refreshParticipants();
  }

  refreshSystem() {
    this.systemService
      .getSystem()
      .subscribe({
        next: (system: System) => {
          this.system = system;
          this.absolute_seatnumbers = system.seatnumbers_absolute;
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

  refreshIpPools() {
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

  creaditTable() {
    this.createTableDialog.hide();
    this.refreshTables();
  }

  selectTable(event: any) {
    if (event) {
      if (event.data) this.selectedTable = event.data;
      else this.selectedTable = event;
    }
    else {
      this.selectedTable = undefined;
    }
  }

  setAbsoluteSeatnumbers(enable: boolean) {
    this.systemService
      .setAbsoluteSeatnumbers(enable)
      .subscribe({
        next: () => {
          this.refreshSystem();
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

}
