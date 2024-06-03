import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SettingService } from 'src/app/services/setting.service';
import { Setting } from 'src/app/interfaces/setting';

@Component({
  selector: 'app-settings-screen',
  templateUrl: './settings-screen.component.html',
  styleUrls: ['./settings-screen.component.scss']
})
export class SettingsScreenComponent implements OnInit {
  absolute_seatnumbers: boolean = false;
  nlpt_sso: boolean = false;
  sso_login_url: string = "https://nlpt.online/app/event-login?redirect=";
  sso_onboarding_url: string = "https://nlpt.online/api/onboarding/2024";

  constructor(
    private errorHandler: ErrorHandlerService,
    private settingService: SettingService
  ) {}

  ngOnInit(): void {
    this.refreshSettings();
  }

  refreshSettings() {
    this.settingService
      .getSettings()
      .subscribe({
        next: (settings: Setting[]) => {
          for (let s of settings) {
            switch (s.id) {
              case "absolute_seatnumbers":
                this.absolute_seatnumbers = s.value;
                break;
              case "nlpt_sso":
                this.nlpt_sso = s.value;
                break;
              case "sso_login_url":
                this.sso_login_url = s.value;
                break;
              case "sso_onboarding_url":
                this.sso_onboarding_url = s.value;
                break;
            }
          }
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  save_nlpt_sso() {
    this.settingService
      .updateSetting("nlpt_sso", this.nlpt_sso)
      .subscribe({
        next: () => {
          if (this.nlpt_sso) {
            this.settingService
              .updateSetting("sso_login_url", this.sso_login_url)
              .subscribe({
                next: () => {
                  this.settingService
                    .updateSetting("sso_onboarding_url", this.sso_onboarding_url)
                    .subscribe({
                      next: () => {
                        this.refreshSettings();
                      },
                      error: (err: HttpErrorResponse) => {
                        this.errorHandler.handleError(err);
                      }
                    })
                },
                error: (err: HttpErrorResponse) => {
                  this.errorHandler.handleError(err);
                }
              })
          }
          else this.refreshSettings();
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  save_absolute_seatnumbers() {
    this.settingService
      .updateSetting("absolute_seatnumbers", this.absolute_seatnumbers)
      .subscribe({
        next: () => {
          this.refreshSettings();
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

}
