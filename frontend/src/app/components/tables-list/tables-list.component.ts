import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Seat } from 'src/app/interfaces/seat';
import { Switch } from 'src/app/interfaces/switch';
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
export class TablesListComponent implements OnChanges {
  @Input() tables!: Table[];
  @Input() ippools!: IpPool[];
  @Input() switches!: Switch[];
  @Input() vlans!: Vlan[];
  @Input() seats!: Seat[];
  @Output() editedTableEvent = new EventEmitter<null>();
  @Output() editedSeatEvent = new EventEmitter<null>();

  editDialog: boolean = false;
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
  }

  editTable(table: Table) {
    this.selectedTable = table;
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

  addSeats(table: Table) {
    let maxNumber: number = 0;
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      if (seat.table_id == table.id && seat.number > maxNumber) maxNumber = seat.number;
    }
    this.seatService
      .createSeat(maxNumber + 1, 'doRandom', table.id)
      .subscribe({
        next: (response: any) => {
          this.editedSeatEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  delSeats(table: Table) {
    let maxSeat: Seat | undefined;
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      if (seat.table_id == table.id) {
        if (maxSeat && seat.number > maxSeat.number) maxSeat = seat;
        else maxSeat = seat;
      }
    }
    if (maxSeat) {
      this.seatService
        .deleteSeat(maxSeat.id)
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
