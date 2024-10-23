import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output, ViewChild } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Table } from 'src/app/interfaces/table';
import { Participant } from 'src/app/interfaces/participant';
import { Seat } from 'src/app/interfaces/seat';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ParticipantService } from 'src/app/services/participant.service';
import { System } from 'src/app/interfaces/system';

@Component({
  selector: 'app-participants-list',
  templateUrl: './participants-list.component.html',
  styleUrls: ['./participants-list.component.scss']
})
export class ParticipantsListComponent implements OnChanges {
  @Input() system?: System;
  @Input() participants!: Participant[];
  @Input() seats!: Seat[];
  @Input() tables!: Table[];
  @Output() editedParticipantEvent = new EventEmitter<null>();

  @ViewChild('editname') editNameDialog: any;
  @ViewChild('editlogin') editLoginDialog: any;
  @ViewChild('editpw') editPwDialog: any;
  @ViewChild('editseatid') editSeatIdDialog: any;
  selectedParticipant: Participant | undefined = undefined;
  newName: string = "";
  newLogin: string | null = "";
  newPw: string | null = "";
  newSeatId: string | null = null;

  seatsOptions: any[] = [];
  tablesById: Map<string, Table> = new Map<string, Table>;
  seatsNames: Map<string, string> = new Map<string, string>;
  absolute_seatnumbers: boolean = false;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private participantService: ParticipantService
  ) {}

  ngOnChanges(): void {
    if (this.system) this.absolute_seatnumbers = this.system.seatnumbers_absolute;
    let maxTable: number = 0;
    for (let i = 0; i < this.tables.length; i++) {
      let table: Table = this.tables[i];
      if (table.number > maxTable) maxTable = table.number;
      this.tablesById.set(table.id, table);
    }
    let list: any[] = [];
    for (let ti = 0; ti < maxTable + 1; ti++) {
      let maxSeat = 0;
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        let table: Table | undefined = this.tablesById.get(seat.table_id);
        if (table && table.number == ti) {
          if (seat.number > maxSeat) maxSeat = seat.number;
        }
      }
      for (let si = 1; si < maxSeat + 1; si++) {
        for (let i = 0; i < this.seats.length; i++) {
          let seat: Seat = this.seats[i];
          let table: Table | undefined = this.tablesById.get(seat.table_id);
          if (table && table.number == ti && seat.number == si) {
            let name: string = '';
            if (table.desc != '') name += table.desc;
            else name += table.number;
            name += ': #' + seat.number;
            if (this.absolute_seatnumbers) name = seat.number_absolute + ' (' + name + ')';
            list.push({name: name, code: seat.id});
            this.seatsNames.set(seat.id, name);
          }
        }
      }
    }
    this.seatsOptions = list;
  }

  editLoginStart(participant: Participant, event: any) {
    this.selectedParticipant = participant;
    if (participant.login) this.newLogin = participant.login;
    else this.newLogin = "";
    this.editLoginDialog.show(event);
  }

  editLogin() {
    this.editLoginDialog.hide();
    if (this.selectedParticipant) {
      this.participantService
        .updateLogin(this.selectedParticipant.id, this.newLogin)
        .subscribe({
          next: (response: any) => {
            this.editedParticipantEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
            if (this.errorHandler.elementError) {
              this.messageService.add({
                severity: 'error',
                summary: $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`,
                detail: $localize `:@@ElementErrorCode2DetailOnParticipant:the given Login name is allready used on a different Participant`,
                life: 6000
              });
            }
          }
        })
    }
    this.selectedParticipant = undefined;
  }

  deleteLogin(participant: Participant) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Login name for Participant ' + participant.name,
      accept: () => {
        this.selectedParticipant = participant;
        this.newLogin = null;
        this.editLogin();
      }
    });
  }

  setAdmin(participant: Participant, admin: boolean) {
    this.participantService
      .updateAdmin(participant.id, admin)
      .subscribe({
        next: (response: any) => {
          this.editedParticipantEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  editPwStart(participant: Participant, event: any) {
    this.selectedParticipant = participant;
    this.newPw = "";
    this.editPwDialog.show(event);
  }

  editPw() {
    this.editPwDialog.hide();
    if (this.selectedParticipant) {
      this.participantService
        .updatePw(this.selectedParticipant.id, this.newPw)
        .subscribe({
          next: (response: any) => {
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedParticipant = undefined;
  }

  deletePw(participant: Participant) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Password for Participant ' + participant.name,
      accept: () => {
        this.selectedParticipant = participant;
        this.newPw = null;
        this.editPw();
      }
    });
  }

  editNameStart(participant: Participant, event: any) {
    this.selectedParticipant = participant;
    this.newName = participant.name;
    this.editNameDialog.show(event);
  }

  editName() {
    this.editNameDialog.hide();
    if (this.selectedParticipant) {
      this.participantService
        .updateName(this.selectedParticipant.id, this.newName)
        .subscribe({
          next: (response: any) => {
            this.editedParticipantEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedParticipant = undefined;
  }

  deleteParticipant(participant: Participant) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Participant ' + participant.name,
      accept: () => {
        this.participantService
          .deleteParticipant(participant.id)
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

  editSeatIdStart(participant: Participant, event: any) {
    this.selectedParticipant = participant;
    if (participant.seat_id) this.newSeatId = participant.seat_id;
    else this.newSeatId = null;
    this.editSeatIdDialog.show(event);
  }

  editSeatIdCheck() {
    if (this.selectedParticipant) {
      let havingParticipant: Participant | null = null;
      if (this.newSeatId) {
        for (let i = 0; i < this.participants.length; i++) {
          let participant: Participant = this.participants[i];
          if (participant.seat_id == this.newSeatId) {
            havingParticipant = participant;
            break;
          }
        }
      }
      if (havingParticipant) {
        this.confirmationService.confirm({
          message: 'Seat is allready used by Participant ' + havingParticipant.name + ' do you want to reassign Seat to Participant ' + this.selectedParticipant!.name,
          accept: () => {
            this.participantService
              .updateSeatId(havingParticipant!.id, null)
              .subscribe({
                next: (response: any) => {
                  this.editSeatId();
                },
                error: (err: HttpErrorResponse) => {
                  this.errorHandler.handleError(err);
                }
              })
          }
        });
      }
      else this.editSeatId();
    }
  }

  editSeatId() {
    this.editSeatIdDialog.hide();
    if (this.selectedParticipant) {
      this.participantService
        .updateSeatId(this.selectedParticipant.id, this.newSeatId)
        .subscribe({
          next: (response: any) => {
            this.editedParticipantEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
            if (this.errorHandler.elementError) {
              if (this.errorHandler.elementErrors.seat_id) {
                if (this.errorHandler.elementErrors.seat_id.code === 70)
                  this.messageService.add({
                    severity: 'error',
                    summary: $localize `:@@ElementErrorCode70Summary:not found`,
                    detail: $localize `:@@ElementErrorCode70:there is no Seat with this ID`,
                    life: 6000
                  });
                if (this.errorHandler.elementErrors.seat_id.code === 2)
                  this.messageService.add({
                    severity: 'error',
                    summary: $localize `:@@ElementErrorCode2SummaryOnParticipant:Seat not available`,
                    detail: $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`,
                    life: 6000
                  });
              }
            }
          }
        })
    }
    this.selectedParticipant = undefined;
  }

  deleteSeatId(participant: Participant) {
    this.confirmationService.confirm({
      message: 'Are you sure that you want to delete Seat for Participant ' + participant.name,
      accept: () => {
        this.selectedParticipant = participant;
        this.newSeatId = null;
        this.editSeatId();
      }
    });
  }
}
