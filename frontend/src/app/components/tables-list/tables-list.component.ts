import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges, OnInit } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Seat } from 'src/app/interfaces/seat';
import { Switch } from 'src/app/interfaces/switch';
import { System } from 'src/app/interfaces/system';
import { Table } from 'src/app/interfaces/table';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SeatService } from 'src/app/services/seat.service';
import { TableService } from 'src/app/services/table.service';

@Component({
  selector: 'app-tables-list',
  templateUrl: './tables-list.component.html',
  styleUrls: ['./tables-list.component.scss']
})
export class TablesListComponent implements OnInit, OnChanges {
  @Input() system?: System;
  @Input() tables!: Table[];
  @Input() ippools!: IpPool[];
  @Input() switches!: Switch[];
  @Input() vlans!: Vlan[];
  @Input() seats!: Seat[];
  @Output() editedTableEvent = new EventEmitter<null>();
  @Output() editedSeatEvent = new EventEmitter<null>();
  @Output() selectTableEvent = new EventEmitter<Table | undefined>();

  absolute_seatnumbers: boolean = false;
  editDialog: boolean = false;
  addSeatsDialog: boolean = false;
  delSeatsDialog: boolean = false;
  numberSeatsDialog: boolean = false;
  adddelSeatsCount: number = 0;
  addSeatNumber: number = 0;
  numberSeatsAsc: boolean = true;
  selectedTable!: Table;

  ippoolsNames: Map<string, string> = new Map<string, string>;
  switchesNames: Map<string, string> = new Map<string, string>;
  seatCounts: Map<string, number> = new Map<string, number>;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private tableService: TableService,
    private seatService: SeatService
  ) {}

  ngOnInit(): void {
    if (this.system) this.absolute_seatnumbers = this.system.seatnumbers_absolute;
  }

  ngOnChanges(): void {
    for (let i = 0; i < this.ippools.length; i++) {
      let ippool = this.ippools[i];
      this.ippoolsNames.set(ippool.id, ippool.desc);
    }
    for (let i = 0; i < this.switches.length; i++) {
      let sw = this.switches[i];
      this.switchesNames.set(sw.id, sw.addr);
    }
    for (let i = 0; i < this.tables.length; i++) {
      this.seatCounts.set(this.tables[i].id, 0);
    }
    for (let i = 0; i < this.seats.length; i++) {
      let table_id: string = this.seats[i].table_id;
      let newVal: number = 1;
      let storedVal: number | undefined = this.seatCounts.get(table_id);
      if (storedVal) newVal = storedVal + 1;
      this.seatCounts.set(table_id, newVal);
    }
    if (this.system) this.absolute_seatnumbers = this.system.seatnumbers_absolute;
  }

  selectTable(selection: Table | undefined) {
    this.selectTableEvent.emit(selection);
  }

  editTable(table: Table) {
    this.selectedTable = table;
    this.selectTableEvent.emit(table);
    this.editDialog = true;
  }

  editedTable() {
    this.editDialog = false;
    this.editedTableEvent.emit(null);
  }

  confirmDelete(table: Table) {
    this.confirmationService.confirm({
        message: 'Are you sure that you want to delete Table ' + table.number + ': ' + table.desc,
        accept: () => {
          this.tableService
            .deleteTable(table.id)
            .subscribe({
              next: (response: any) => {
                this.editedTableEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
                let detail: string = $localize `:@@DeleteErrorGeneric:Unknown error`;
                if (this.errorHandler.elementError) {
                  if (this.errorHandler.elementErrors.code == 3)
                    detail = $localize `:@@DeleteErrorCode3OnTable:Can't delete Table. There is at least one Seat attached to Table ` + table.number + ': ' + table.desc;
                }
                this.messageService.add({
                  severity: 'error',
                  summary: $localize `:@@DeleteErrorSummary:deletion not possible`,
                  detail: detail,
                  life: 6000
                });
              }
            })
        }
    });
  }

  numberSeatsStart(table: Table) {
    this.selectedTable = table;
    this.selectTableEvent.emit(table);
    this.adddelSeatsCount = 0;
    this.numberSeatsDialog = true;
  }

  numberSeats() {
    this.numberSeatsDialog = false;
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      if (seat.table_id == this.selectedTable.id) {
        this.seatService
          .updateAbsoluteNumber(seat.id, null)
          .subscribe({
            next: () => {},
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
    }
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      if (seat.table_id == this.selectedTable.id) {
        let absNumber: number = 0;
        if (this.numberSeatsAsc) absNumber = this.adddelSeatsCount + (seat.number - 1);
        else absNumber = this.adddelSeatsCount - (seat.number - 1);
        if (absNumber >= 0) {
          this.seatService
            .updateAbsoluteNumber(seat.id, absNumber)
            .subscribe({
              next: () => {
                this.editedSeatEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
              }
            })
        }
      }
    }
  }

  addSeatsStart(table: Table) {
    this.selectedTable = table;
    this.selectTableEvent.emit(table);
    this.adddelSeatsCount = 0;
    this.addSeatNumber = 0;
    this.addSeatsDialog = true;
  }

  addSeat(number: number, pw: string, table_id: string) {
    this.seatService
      .createSeat(number, pw, table_id)
      .subscribe({
        next: (response: any) => {
          this.editedSeatEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          let detail: string = $localize `:@@ElementErrorGeneric:Unknown error`;
          if (this.errorHandler.elementErrors) {
            if (this.errorHandler.elementErrors.number) {
              if (this.errorHandler.elementErrors.number.code == 51)
                detail = $localize `:@@ElementErrorCode51:Number needs to be 1 or bigger`;
              if (this.errorHandler.elementErrors.number.code == 52)
                detail = $localize `:@@ElementErrorCode52:Number allready present on Table`;
              if (this.errorHandler.elementErrors.number.code == 54)
                detail = $localize `:@@ElementErrorCode54:No additional Seats possible on this Table, as this would exceed IpPool range`;
            }
          }
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@ElementErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  addSeats() {
    this.addSeatsDialog = false;
    if (this.addSeatNumber > 0) {
      let pw: string = window.crypto.getRandomValues(new BigUint64Array(1))[0].toString(36).slice(0, 8);
      this.addSeat(this.addSeatNumber, pw, this.selectedTable.id);
    }
    if (this.adddelSeatsCount > 0) {
      let maxNumber: number = 0;
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        if (seat.table_id == this.selectedTable.id && seat.number > maxNumber) maxNumber = seat.number;
      }
      for (let i = 0; i < this.adddelSeatsCount; i++) {
        let pw: string = window.crypto.getRandomValues(new BigUint64Array(1))[0].toString(36).slice(0, 8);
        this.addSeat(maxNumber + 1 + i, pw, this.selectedTable.id);
      }
    }
  }

  delSeatsStart(table: Table) {
    this.selectedTable = table;
    this.selectTableEvent.emit(table);
    this.adddelSeatsCount = 0;
    this.delSeatsDialog = true;
  }

  delSeats() {
    this.delSeatsDialog = false;
    let seatIds: Map<number, string> = new Map<number, string>;
    let maxNumber: number = 0;
    let maxSeat: Seat | undefined;
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      if (seat.table_id == this.selectedTable.id) {
        seatIds.set(seat.number, seat.id);
        if (seat.number > maxNumber) maxNumber = seat.number;
      }
    }
    for (let i = 0; i < this.adddelSeatsCount; i++) {
      let seatId: string | undefined = seatIds.get(maxNumber - i);
      if (seatId) {
        this.seatService
        .deleteSeat(seatId)
        .subscribe({
          next: (response: any) => {
            this.editedSeatEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
      }
    }
  }
}
