import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, ViewChild } from '@angular/core';
import { Participant } from 'src/app/interfaces/participant';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ParticipantService } from 'src/app/services/participant.service';

@Component({
  selector: 'app-participants-screen',
  templateUrl: './participants-screen.component.html',
  styleUrls: ['./participants-screen.component.scss']
})
export class ParticipantsScreenComponent implements OnInit {
  participants: Participant[] = [];

  @ViewChild('addSingleParticipant') addSingleParticipantDialog: any;

  addMultiParticipantsDialog: boolean = false;
  newParticipantName: string = "";

  constructor(
    private errorHandler: ErrorHandlerService,
    private participantService: ParticipantService
  ) { }

  ngOnInit(): void {
    this.refreshParticipants();
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
