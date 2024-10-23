import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, ViewChild } from '@angular/core';
import { Table } from 'src/app/interfaces/table';
import { Participant } from 'src/app/interfaces/participant';
import { Seat } from 'src/app/interfaces/seat';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ParticipantService } from 'src/app/services/participant.service';
import { SeatService } from 'src/app/services/seat.service';
import { TableService } from 'src/app/services/table.service';
import { SystemService } from 'src/app/services/system.service';
import { System } from 'src/app/interfaces/system';

@Component({
  selector: 'app-participants-screen',
  templateUrl: './participants-screen.component.html',
  styleUrls: ['./participants-screen.component.scss']
})
export class ParticipantsScreenComponent implements OnInit {
  system!: System;
  participants: Participant[] = [];
  seats: Seat[] = [];
  tables: Table[] = [];

  @ViewChild('addSingleParticipant') addSingleParticipantDialog: any;

  addMultiParticipantsDialog: boolean = false;
  newParticipantName: string = "";

  constructor(
    private errorHandler: ErrorHandlerService,
    private participantService: ParticipantService,
    private seatService: SeatService,
    private tableService: TableService,
    private systemService: SystemService
  ) { }

  ngOnInit(): void {
    this.refreshSystem();
    this.refreshParticipants();
    this.refreshSeats();
    this.refreshTables();
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

  creaditParticipant() {
    this.refreshParticipants();
  }

  addMultiParticipantsStart() {
    this.addMultiParticipantsDialog = true;
  }

  createParticipant() {
    let multi: boolean = false;
    if (this.addMultiParticipantsDialog) {
      multi = true;
      this.addMultiParticipantsDialog = false;
    }
    else this.addSingleParticipantDialog.hide();
    this.participantService
      .createParticipant(this.newParticipantName)
      .subscribe({
        next: () => {
          this.refreshParticipants();
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
    this.newParticipantName = "";
    if (multi) this.addMultiParticipantsDialog = true;
  }

}
