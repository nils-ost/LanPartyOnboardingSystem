import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { Message } from 'primeng/api';
import { Subscription, timer } from 'rxjs';
import { Onboarding } from 'src/app/interfaces/onboarding';
import { Setting } from 'src/app/interfaces/setting';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { OnboardingService } from 'src/app/services/onboarding.service';
import { SettingService } from 'src/app/services/setting.service';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.component.html',
  styleUrls: ['./onboarding.component.scss']
})
export class OnboardingComponent implements OnInit, OnDestroy {
  @Output() onboardingChangeEvent = new EventEmitter<Onboarding | undefined>;

  refreshOnboardingTimer = timer(5000, 5000);
  refreshOnboardingTimerSubscription: Subscription | undefined;
  onlineCheckTimer = timer(2000, 1000);
  onlineCheckTimerSubscription: Subscription | undefined;

  onboarding?: Onboarding;
  absolute_seatnumbers: boolean = false;
  sso_onboarding: boolean = false;
  errorMsg: Message[] = [];
  selectedTable: number | undefined;
  selectedSeat: number | undefined;
  selectedPw: string | undefined;
  tokenFetched: boolean = false;
  doneOnline: boolean = false;  // if onboarding is done and the online-check was successful, this gets true

  constructor(
    private errorHandler: ErrorHandlerService,
    private settingService: SettingService,
    private onboardingService: OnboardingService,
    public utils: UtilsService
  ) {}

  ngOnInit(): void {
    this.settingService.getSetting('absolute_seatnumbers').subscribe({
        next: (setting: Setting) => {this.absolute_seatnumbers = setting.value;},
        error: (err: HttpErrorResponse) => {this.errorHandler.handleError(err);}
    })
    this.refreshOnboarding();
  }

  ngOnDestroy(): void {
    this.disableAutoRefresh();
  }

  disableAutoRefresh() {
    this.refreshOnboardingTimerSubscription?.unsubscribe();
  }

  refreshOnboarding() {
    this.errorMsg = [];
    let token = window.location.search.split('token=').pop()?.split('&')[0];
    if (token && !this.tokenFetched) {
      this.sso_onboarding = true;
      this.onboardingService
        .ssoOnboarding(token)
        .subscribe({
          next: (onboarding: Onboarding) => {
            this.onboarding = onboarding;
            this.tokenFetched = true;
            this.onboardingChangeEvent.emit(this.onboarding);
            if (onboarding.done) this.onlineCheck();
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
            if (this.errorHandler.elementError) this.translateErrorCode(this.errorHandler.elementErrors);
          }
        })
    }
    else
      this.onboardingService
        .getOnboarding()
        .subscribe({
          next: (onboarding: Onboarding) => {
            this.refreshOnboardingTimerSubscription?.unsubscribe();
            this.onboarding = onboarding;
            this.onboardingChangeEvent.emit(this.onboarding);
            if (onboarding.done) this.onlineCheck();
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
            if (this.errorHandler.elementError) {
              this.translateErrorCode(this.errorHandler.elementErrors);
              if (this.errorHandler.elementErrors.code === 6 && this.refreshOnboardingTimerSubscription == undefined) {
                this.refreshOnboardingTimerSubscription = this.refreshOnboardingTimer.subscribe(() => this.refreshOnboarding());
              }
            }
          }
        })
  }

  sendSeatParameters() {
    if ((this.absolute_seatnumbers || this.selectedTable) && this.selectedSeat && this.selectedPw) {
      this.errorMsg = [];
      let table: number = 0;
      if (!this.absolute_seatnumbers && this.selectedTable) table = this.selectedTable;
      this.onboardingService
        .startOnboarding(table, this.selectedSeat, this.selectedPw)
        .subscribe({
          next: (onboarding: Onboarding) => {
            this.onboarding = onboarding;
            this.onboardingChangeEvent.emit(this.onboarding);
            if (onboarding.done) this.onlineCheck();
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
          if (onboarding.done) this.onlineCheck();
        },
        error: (err: HttpErrorResponse) => {
          this.onboarding = undefined;
          this.onboardingChangeEvent.emit(this.onboarding);
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.translateErrorCode(this.errorHandler.elementErrors);
        }
      })
  }

  SSOLoginUrl(): String {
    if (this.onboarding?.login_url) return this.onboarding.login_url + window.location.href;
    else return window.location.href;
  }

  onlineCheck() {
    if (this.onlineCheckTimerSubscription == undefined) {
      this.doneOnline = false;
      this.onlineCheckTimerSubscription = this.onlineCheckTimer.subscribe(() => this.onlineCheck());
      console.log('activated online check')
      return;
    }
    console.log('executing online check')
    this.onboardingService.getOnboarding()
      .subscribe({
        next: (onboarding: Onboarding) => {
            if(onboarding.online == true) {
                this.onlineCheckTimerSubscription?.unsubscribe();
                this.doneOnline = true;
            }
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  translateErrorCode(error: any) {
    let msg: string = "";

    if (error.code === 6) msg = $localize `:@@OnboardingErrorCode6:Your Device is not yet known. Please stand by, this screen will automatically refresh, when your Device is ready for Onboarding.`;
    if (error.code === 7) msg = $localize `:@@OnboardingErrorCode7:Your Device is blocked for onboarding. Please contact an admin.`;
    if (error.code === 8) msg = $localize `:@@OnboardingErrorCode8:Invalid Table number. Please try again.`;
    if (error.code === 9) msg = $localize `:@@OnboardingErrorCode9:Invalid Seat number. Please try again.`;
    if (error.code === 10) msg = $localize `:@@OnboardingErrorCode10:This Seat is allready taken. Please try again or contact an admin.`;
    if (error.code === 11) msg = $localize `:@@OnboardingErrorCode11:Wrong password. Please try again.`;
    if (error.code === 12) msg = $localize `:@@OnboardingErrorCode12:This Seat is not associated to a Participant. Please contact an admin.`;
    if (error.code === 13) msg = $localize `:@@OnboardingErrorCode13:Something went wrong. Please try again.`;
    if (error.code === 14) msg = $localize `:@@OnboardingErrorCode14:Please contact an admin.`;
    if (error.code === 15) msg = $localize `:@@OnboardingErrorCode15:Invalid Login on SSO provider.`;

    if (msg === "") msg = $localize `:@@OnboardingErrorCodeFallback:Unknown error. Please contact an admin.`;
    this.errorMsg = [
      { severity: 'error', summary: 'Error', detail: msg }
    ];
  }

}
