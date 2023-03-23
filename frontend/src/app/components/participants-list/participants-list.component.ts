import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Participant } from 'src/app/interfaces/participant';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ParticipantService } from 'src/app/services/participant.service';

@Component({
  selector: 'app-participants-list',
  templateUrl: './participants-list.component.html',
  styleUrls: ['./participants-list.component.scss']
})
export class ParticipantsListComponent {
  @Input() participants!: Participant[];
  @Output() editedParticipantEvent = new EventEmitter<null>();

  @ViewChild('editname') editNameDialog: any;
  @ViewChild('editlogin') editLoginDialog: any;
  @ViewChild('editpw') editPwDialog: any;
  selectedParticipant: Participant | undefined = undefined;
  newName: string = "";
  newLogin: string | null = "";
  newPw: string | null = "";

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private participantService: ParticipantService
  ) {}

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
}
