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

@Component({
  selector: 'app-tables-screen',
  templateUrl: './tables-screen.component.html',
  styleUrls: ['./tables-screen.component.scss']
})
export class TablesScreenComponent implements OnInit {
  @ViewChild('createtable') createTableDialog: any;
  vlans: Vlan[] = [];
  switches: Switch[] = [];
  ippools: IpPool[] = [];
  tables: Table[] = [];
  seats: Seat[] = [];

  constructor(
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService,
    private switchService: SwitchService,
    private ippoolService: IpPoolService,
    private tableService: TableService,
    private seatService: SeatService
  ) { }

  ngOnInit(): void {
    this.refreshVlans();
    this.refreshSwitches();
    this.refreshIpPools();
    this.refreshTables();
    this.refreshSeats();
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

  creaditTable() {
    this.createTableDialog.hide();
    this.refreshTables();
  }

  creadelSeat() {
    this.refreshSeats();
  }

}
