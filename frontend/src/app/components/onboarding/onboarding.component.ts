import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { Message } from 'primeng/api';
import { Onboarding } from 'src/app/interfaces/onboarding';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { OnboardingService } from 'src/app/services/onboarding.service';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.component.html',
  styleUrls: ['./onboarding.component.scss']
})
export class OnboardingComponent implements OnInit {
  @Output() onboardingChangeEvent = new EventEmitter<Onboarding | undefined>;
  onboarding?: Onboarding;
  errorMsg: Message[] = [];
  selectedTable: number | undefined;
  selectedSeat: number | undefined;
  selectedPw: string | undefined;
  utils: UtilsService = new UtilsService();

  constructor(
    private errorHandler: ErrorHandlerService,
    private onboardingService: OnboardingService
  ) {}

  ngOnInit(): void {
    this.refreshOnboarding();
  }

  refreshOnboarding() {
    this.onboardingService
      .getOnboarding()
      .subscribe({
        next: (onboarding: Onboarding) => {
          this.onboarding = onboarding;
          this.onboardingChangeEvent.emit(this.onboarding);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.translateErrorCode(this.errorHandler.elementErrors);
        }
      })
  }

  sendSeatParameters() {
    if (this.selectedTable && this.selectedSeat && this.selectedPw) {
      this.errorMsg = [];
      this.onboardingService
        .startOnboarding(this.selectedTable, this.selectedSeat, this.selectedPw)
        .subscribe({
          next: (onboarding: Onboarding) => {
            this.onboarding = onboarding;
            this.onboardingChangeEvent.emit(this.onboarding);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
            if (this.errorHandler.elementError) this.translateErrorCode(this.errorHandler.elementErrors);
          }
        })
    }
  }

  sendParticipantConfirmation(selection: boolean) {
    this.errorMsg = [];
    this.onboardingService
      .completeOnboarding(selection)
      .subscribe({
        next: (onboarding: Onboarding) => {
          this.onboarding = onboarding;
          this.onboardingChangeEvent.emit(this.onboarding);
        },
        error: (err: HttpErrorResponse) => {
          this.onboarding = undefined;
          this.onboardingChangeEvent.emit(this.onboarding);
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.translateErrorCode(this.errorHandler.elementErrors);
        }
      })
  }

  translateErrorCode(error: any) {
    let msg: string = "";

    if (error.code === 6) msg = $localize `:@@OnboardingErrorCode6:Your Device is unknown. Please contact an admin.`;
    if (error.code === 7) msg = $localize `:@@OnboardingErrorCode7:Your Device is blocked for onboarding. Please contact an admin.`;
    if (error.code === 8) msg = $localize `:@@OnboardingErrorCode8:Invalid Table number. Please try again.`;
    if (error.code === 9) msg = $localize `:@@OnboardingErrorCode9:Invalid Seat number. Please try again.`;
    if (error.code === 10) msg = $localize `:@@OnboardingErrorCode10:This Seat is allready taken. Please try again or contact an admin.`;
    if (error.code === 11) msg = $localize `:@@OnboardingErrorCode11:Wrong password. Please try again.`;
    if (error.code === 12) msg = $localize `:@@OnboardingErrorCode12:This Seat is not associated to a Participant. Please contact an admin.`;
    if (error.code === 13) msg = $localize `:@@OnboardingErrorCode13:Something went wrong. Please try again.`;
    if (error.code === 14) msg = $localize `:@@OnboardingErrorCode14:Please contact an admin.`;

    if (msg === "") msg = $localize `:@@OnboardingErrorCodeFallback:Unknown error. Please contact an admin.`;
    this.errorMsg = [
      { severity: 'error', summary: 'Error', detail: msg }
    ];
  }

}
