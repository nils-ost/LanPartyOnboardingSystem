import { Component, EventEmitter, Input, Output, OnChanges, ViewChild, OnInit } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { Seat } from 'src/app/interfaces/seat';
import { SeatService } from 'src/app/services/seat.service';
import { Table } from 'src/app/interfaces/table';
import { HttpErrorResponse } from '@angular/common/http';
import { Participant } from 'src/app/interfaces/participant';
import { ParticipantService } from 'src/app/services/participant.service';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { UtilsService } from 'src/app/services/utils.service';
import { SettingService } from 'src/app/services/setting.service';

@Component({
  selector: 'app-seats-list',
  templateUrl: './seats-list.component.html',
  styleUrls: ['./seats-list.component.scss']
})
export class SeatsListComponent implements OnChanges, OnInit {
  @Input() tables!: Table[];
  @Input() seats!: Seat[];
  @Input() ippools!: IpPool[];
  @Input() participants!: Participant[];
  @Input() selectedTable?: Table;
  @Output() editedSeatEvent = new EventEmitter<null>();
  @Output() editedParticipantEvent = new EventEmitter<null>();

  @ViewChild('editpassword') editPasswordDialog: any;
  @ViewChild('editparticipant') editParticipantDialog: any;
  @ViewChild('editabsolutenumber') editAbsoluteNumberDialog: any;
  multiSortMeta: any[] = [];

  participantsOptions: any[] = [];
  displaySeats: any[] = [];
  selectedSeat: Seat | undefined;
  newPassword: string = "";
  newParticipantId: string | null = null;
  newAbsoluteNumber: number | null = null;
  tablesNumbers: Map<string, number> = new Map<string, number>;
  tableStartIp: Map<string, number> = new Map<string, number>;
  participantsNameBySeat: Map<string, string> = new Map<string, string>;
  participantsBySeat: Map<string, Participant> = new Map<string, Participant>;
  participantsById: Map<string, Participant> = new Map<string, Participant>;
  seatsById: Map<string, Seat> = new Map<string, Seat>;
  absolute_seatnumbers: boolean = false;

  constructor(
    private messageService: MessageService,
    private settingService: SettingService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private seatService: SeatService,
    private participantService: ParticipantService,
    private utils: UtilsService
  ) {}

  ngOnInit(): void {
    this.multiSortMeta.push({field: 'table', order: 1});
    this.multiSortMeta.push({field: 'seatNumber', order: 1});
    this.absolute_seatnumbers = this.settingService.getValue('absolute_seatnumbers');
  }

  ngOnChanges(): void {
    for (let i = 0; i < this.tables.length; i++) {
      let table: Table = this.tables[i];
      this.tablesNumbers.set(table.id, table.number);
    }

    for (let i = 0; i < this.tables.length; i++) {
      let table: Table = this.tables[i];
      for (let j = 0; j < this.ippools.length; j++) {
        let pool: IpPool = this.ippools[j];
        if (pool.id == table.seat_ip_pool_id) {
          this.tableStartIp.set(table.id, pool.range_start);
          break;
        }
      }
    }

    this.seatsById.clear();
    for (let i = 0; i < this.seats.length; i++) {
      let seat: Seat = this.seats[i];
      this.seatsById.set(seat.id, seat);
    }
    let newList: any[] = [];
    if (this.selectedTable) {
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        if (this.selectedTable.id == seat.table_id) {
          let element = {
            table: this.tablesNumbers.get(seat.table_id),
            seatNumber: seat.number,
            seatIp: this.seatIpStr(seat.number, seat.table_id),
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
          seatIp: this.seatIpStr(seat.number, seat.table_id),
          seat: seat
        }
        newList.push(element);
      }
    }
    this.displaySeats = newList;
    this.participantsNameBySeat.clear();
    this.participantsBySeat.clear();
    this.participantsById.clear();
    let list: any[] = [];
    for (let i = 0; i < this.participants.length; i++) {
      let participant: Participant = this.participants[i];
      this.participantsById.set(participant.id, participant);
      if (participant.seat_id) {
        this.participantsNameBySeat.set(participant.seat_id, participant.name);
        this.participantsBySeat.set(participant.seat_id, participant);
      }
      list.push({name: participant.name, code: participant.id});
    }
    this.participantsOptions = list;
  }

  seatIpStr(seat_nb: number, table_id: string): string {
    let ip: number | undefined = this.tableStartIp.get(table_id);
    if (ip) {
      return this.utils.ip_int_to_str(ip + seat_nb - 1);
    }
    else {
      return '';
    }
  }

  deleteSeat(seat: Seat) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Seat ' + seat.number + ' on Table ' + this.tablesNumbers.get(seat.table_id),
      accept: () => {
        this.seatService
          .deleteSeat(seat.id)
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

  deleteAbsoluteNumber(seat: Seat) {
    this.seatService
      .updateAbsoluteNumber(seat.id, null)
      .subscribe({
        next: () => {
          this.editedSeatEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  editAbsoluteNumberStart(seat: Seat, event: any) {
    this.selectedSeat = seat;
    if (seat.number_absolute) this.newAbsoluteNumber = seat.number_absolute;
    else this.newAbsoluteNumber = null;
    this.editAbsoluteNumberDialog.show(event);
  }

  editAbsoluteNumber() {
    if (this.selectedSeat) {
      this.seatService
        .updateAbsoluteNumber(this.selectedSeat.id, this.newAbsoluteNumber)
        .subscribe({
          next: () => {
            this.editedSeatEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedSeat = undefined;
    this.editAbsoluteNumberDialog.hide();
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

  editParticipantStart(seat: Seat, participant: Participant | undefined, event: any) {
    this.selectedSeat = seat;
    if (participant) this.newParticipantId = participant.id;
    else this.newParticipantId = null;
    this.editParticipantDialog.show(event);
  }

  editParticipantCheck() {
    if (this.selectedSeat && this.newParticipantId) {
      let participant: Participant | undefined = this.participantsById.get(this.newParticipantId);
      if (participant) {
        if (participant.seat_id) {
          let havingSeat: Seat | undefined = this.seatsById.get(participant.seat_id);
          if (havingSeat) {
            this.confirmationService.confirm({
              message: 'Are you sure that you want to reseat ' + participant.name +  ' from Seat ' + havingSeat.number + ' on Table ' + this.tablesNumbers.get(havingSeat.table_id) + ' to Seat ' + this.selectedSeat.number + ' on Table ' + this.tablesNumbers.get(this.selectedSeat.table_id),
              accept: () => {
                this.editParticipant();
              }
            });
          }
        }
        else this.editParticipant();
      }
    }
  }

  editParticipant() {
    if (this.selectedSeat && this.newParticipantId) {
      let participant: Participant | undefined = this.participantsById.get(this.newParticipantId);
      if (participant) {
        this.participantService
          .updateSeatId(participant.id, this.selectedSeat.id)
          .subscribe({
            next: (response: any) => {
              this.editedParticipantEvent.emit(null);
            },
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
    }
    this.selectedSeat = undefined;
    this.editParticipantDialog.hide();
  }

  deleteParticipant(seat: Seat, participant: Participant | undefined) {
    if (participant) {
      this.confirmationService.confirm({
        message: 'Are you sure that you want to delete Participant for Seat ' + seat.number + ' on Table ' + this.tablesNumbers.get(seat.table_id),
        accept: () => {
          this.participantService
            .updateSeatId(participant.id, null)
            .subscribe({
              next: (response: any) => {
                this.editedParticipantEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
              }
            })
        }
      });
    }
  }
}
