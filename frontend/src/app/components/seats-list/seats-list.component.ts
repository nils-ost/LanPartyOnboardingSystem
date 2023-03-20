import { Component, EventEmitter, Input, Output, OnChanges, ViewChild, OnInit } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { Seat } from 'src/app/interfaces/seat';
import { SeatService } from 'src/app/services/seat.service';
import { Table } from 'src/app/interfaces/table';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-seats-list',
  templateUrl: './seats-list.component.html',
  styleUrls: ['./seats-list.component.scss']
})
export class SeatsListComponent implements OnChanges, OnInit {
  @Input() tables!: Table[];
  @Input() seats!: Seat[];
  @Input() selectedTable?: Table;
  @Output() editedSeatEvent = new EventEmitter<null>();

  @ViewChild('editpassword') editPasswordDialog: any;
  multiSortMeta: any[] = [];

  displaySeats: any[] = [];
  selectedSeat: Seat | undefined;
  newPassword: string = "";
  tablesNumbers: Map<string, number> = new Map<string, number>;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private seatService: SeatService
  ) {}

  ngOnInit(): void {
    this.multiSortMeta.push({field: 'table', order: 1});
    this.multiSortMeta.push({field: 'seatNumber', order: 1});
  }

  ngOnChanges(): void {
    for (let i = 0; i < this.tables.length; i++) {
      let table: Table = this.tables[i];
      this.tablesNumbers.set(table.id, table.number);
    }

    let newList: any[] = [];
    if (this.selectedTable) {
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        if (this.selectedTable.id == seat.table_id) {
          let element = {
            table: this.tablesNumbers.get(seat.table_id),
            seatNumber: seat.number,
            seat: seat
          }
          newList.push(element);
        }
      }
    }
    else {
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        let element = {
          table: this.tablesNumbers.get(seat.table_id),
          seatNumber: seat.number,
          seat: seat
        }
        newList.push(element);
      }
    }
    this.displaySeats = newList;
  }

  deletePw(seat: Seat) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Password for Seat ' + seat.number + ' on Table ' + this.tablesNumbers.get(seat.table_id),
      accept: () => {
        this.seatService
          .updatePw(seat.id, null)
          .subscribe({
            next: (response: any) => {
              this.editedSeatEvent.emit(null);
            },
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
    });
  }

  generatePw(seat: Seat) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to generate a new Password for Seat ' + seat.number + ' on Table ' + this.tablesNumbers.get(seat.table_id),
      accept: () => {
        let pw: string = window.crypto.getRandomValues(new BigUint64Array(1))[0].toString(36).slice(0, 8);
        this.seatService
          .updatePw(seat.id, pw)
          .subscribe({
            next: (response: any) => {
              this.editedSeatEvent.emit(null);
            },
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
    });
  }

  editPasswordStart(seat: Seat, event: any) {
    this.selectedSeat = seat;
    if (seat.pw) this.newPassword = seat.pw;
    else this.newPassword = "";
    this.editPasswordDialog.show(event);
  }

  editPassword() {
    if (this.selectedSeat) {
      this.seatService
        .updatePw(this.selectedSeat.id, this.newPassword)
        .subscribe({
          next: (response: any) => {
            this.editedSeatEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedSeat = undefined;
    this.editPasswordDialog.hide();
  }
}
