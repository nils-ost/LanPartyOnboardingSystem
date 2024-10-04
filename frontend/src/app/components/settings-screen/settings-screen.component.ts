import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SettingService } from 'src/app/services/setting.service';
import { Setting } from 'src/app/interfaces/setting';
import { Switch } from 'src/app/interfaces/switch';
import { PortService } from 'src/app/services/port.service';
import { SwitchService } from 'src/app/services/switch.service';
import { PortConfigCache } from 'src/app/interfaces/port';

@Component({
  selector: 'app-settings-screen',
  templateUrl: './settings-screen.component.html',
  styleUrls: ['./settings-screen.component.scss']
})
export class SettingsScreenComponent implements OnInit {
  switches: Switch[] = [];
  absolute_seatnumbers: boolean = false;
  nlpt_sso: boolean = false;
  pno_loading: boolean = false;
  pno: boolean = false;
  pcc: boolean = false;
  pcc_total: number = 0;
  pcc_commit: number = 0;
  pcc_retreat: number = 0;
  sso_login_url: string = "https://nlpt.online/app/event-login?redirect=";
  sso_onboarding_url: string = "https://nlpt.online/api/onboarding/2024";

  constructor(
    private errorHandler: ErrorHandlerService,
    private settingService: SettingService,
    private portService: PortService,
    private switchService: SwitchService
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

  refreshPortConfigCaches() {
    if (this.pcc) {
      this.pcc_total = 0;
      this.pcc_commit = 0;
      this.pcc_retreat = 0;
      this.portService
        .getCaches()
        .subscribe({
          next: (pccs: PortConfigCache[]) => {
            pccs.forEach((pcc) => {
              this.pcc_total += 1;
              if (pcc.scope == 0) this.pcc_commit += 1;
              else this.pcc_retreat += 1;
            })
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

  refreshSwitches() {
    this.pno_loading = true;
    if (this.pno) {
      this.switchService
        .getSwitches()
        .subscribe({
          next: (switches: Switch[]) => {
            this.switches = switches;
            this.pno_loading = false;
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

  clearPortConfigCaches() {
    if (this.pcc) {
      this.portService
        .deleteAllCaches()
        .subscribe({
          next: () => {
            this.refreshPortConfigCaches();
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
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

  save_pno() {
    for (let i = 0; i < this.switches.length; i++) {
      this.switchService
        .updatePortNumberingOffset(this.switches[i].id, this.switches[i].port_numbering_offset)
        .subscribe({
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
  }

}
