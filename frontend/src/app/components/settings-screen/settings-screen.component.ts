import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SettingService } from 'src/app/services/setting.service';
import { Setting } from 'src/app/interfaces/setting';
import { Switch } from 'src/app/interfaces/switch';
import { PortService } from 'src/app/services/port.service';
import { SwitchService } from 'src/app/services/switch.service';
import { PortConfigCache } from 'src/app/interfaces/port';
import { SystemService } from 'src/app/services/system.service';
import { DeviceService } from 'src/app/services/device.service';
import { Device } from 'src/app/interfaces/device';
import { timer } from 'rxjs';
import { UtilsService } from 'src/app/services/utils.service';

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
  rod_loading: boolean = false;
  pno: boolean = false;
  pcc: boolean = false;
  rod: boolean = false;
  settings: boolean = false;
  settingsPlayNw: boolean = false;
  pcc_total: number = 0;
  pcc_commit: number = 0;
  pcc_retreat: number = 0;
  rod_total: number = 0;
  rod_offline: number = 0;
  rod_port: number = 0;
  rod_wodesc: number = 0;
  sso_login_url: string = "https://nlpt.online/app/event-login?redirect=";
  sso_onboarding_url: string = "https://nlpt.online/api/onboarding/2024";
  sso_ip_overwrite: string | null = null;
  sso_ip_overwrite_enabled: boolean = false;
  settings_ro: Setting[] = [];
  settings_rw: Setting[] = [];
  settings_play_nw: Setting[] = [];

  vlan_def_ips: boolean = false;
  play_vlan_def_ip: number | null = null;
  play_vlan_def_mask: number = 24;
  mgmt_vlan_def_ip: number | null = null;
  mgmt_vlan_def_mask: number = 24;
  ob_vlan_def_ip: number | null = null;
  ob_vlan_def_mask: number = 24;
  play_vlan_def_ip_oct1: number | undefined;
  play_vlan_def_ip_oct2: number | undefined;
  play_vlan_def_ip_oct3: number | undefined;
  play_vlan_def_ip_oct4: number | undefined;
  mgmt_vlan_def_ip_oct1: number | undefined;
  mgmt_vlan_def_ip_oct2: number | undefined;
  mgmt_vlan_def_ip_oct3: number | undefined;
  mgmt_vlan_def_ip_oct4: number | undefined;
  ob_vlan_def_ip_oct1: number | undefined;
  ob_vlan_def_ip_oct2: number | undefined;
  ob_vlan_def_ip_oct3: number | undefined;
  ob_vlan_def_ip_oct4: number | undefined;
  play_vlan_def_ip_saved: boolean = false;
  mgmt_vlan_def_ip_saved: boolean = false;
  ob_vlan_def_ip_saved: boolean = false;

  constructor(
    private errorHandler: ErrorHandlerService,
    private settingService: SettingService,
    private systemService: SystemService,
    private portService: PortService,
    private switchService: SwitchService,
    private deviceService: DeviceService,
    private utils: UtilsService
  ) {}

  ngOnInit(): void {
    this.refreshSettings();
  }

  refreshSettings() {
    this.settingService
      .getSettings()
      .subscribe({
        next: (settings: Setting[]) => {
          this.settings_ro = [];
          this.settings_rw = [];
          for (let s of settings) {
            switch (s.id) {
              case "absolute_seatnumbers":
                this.absolute_seatnumbers = s.value;
                break;
              case "nlpt_sso":
                this.nlpt_sso = s.value;
                break;
              case "sso_login_url":
                if (s.value != '') this.sso_login_url = s.value;
                break;
              case "sso_onboarding_url":
                if (s.value != '') this.sso_onboarding_url = s.value;
                break;
              case "sso_ip_overwrite":
                this.sso_ip_overwrite = s.value;
                this.sso_ip_overwrite_enabled = this.sso_ip_overwrite != null;
                break;
              case "play_vlan_def_ip":
                this.play_vlan_def_ip = s.value;
                break;
              case "play_vlan_def_mask":
                this.play_vlan_def_mask = s.value;
                break;
              case "mgmt_vlan_def_ip":
                this.mgmt_vlan_def_ip = s.value;
                break;
              case "mgmt_vlan_def_mask":
                this.mgmt_vlan_def_mask = s.value;
                break;
              case "ob_vlan_def_ip":
                this.ob_vlan_def_ip = s.value;
                break;
              case "ob_vlan_def_mask":
                this.ob_vlan_def_mask = s.value;
                break;
              default:
                if (s.ro) this.settings_ro.push(s);
                else if (20 <= s.order && s.order < 30) this.settings_play_nw.push(s);
                else this.settings_rw.push(s);
                break;
            }
          this.settings_rw = this.settings_rw.sort((a, b) => (a.id > b.id) ? 1 : ((a.id < b.id) ? -1 : 0));
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

  refreshDevices() {
    this.rod_loading = true;
    if (this.rod) {
      this.deviceService
        .getDevices()
        .subscribe({
          next: (devices: Device[]) => {
            this.rod_total = devices.length;
            this.rod_offline = 0;
            this.rod_port = 0;
            this.rod_wodesc = 0;
            let currentTs = Math.floor(Date.now() / 1000);
            for (let i = 0; i < devices.length; i++) {
              let device: Device = devices[i];
              if ((currentTs - device.last_scan_ts) > 60) this.rod_offline++;
              if (device.port_id != null) this.rod_port++;
              if (device.desc == '') this.rod_wodesc++;
            }
            this.rod_loading = false;
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

  fillVlanDefIps() {
    if (this.vlan_def_ips) {
      this.play_vlan_def_ip_oct1 = undefined;
      this.play_vlan_def_ip_oct2 = undefined;
      this.play_vlan_def_ip_oct3 = undefined;
      this.play_vlan_def_ip_oct4 = undefined;
      this.mgmt_vlan_def_ip_oct1 = undefined;
      this.mgmt_vlan_def_ip_oct2 = undefined;
      this.mgmt_vlan_def_ip_oct3 = undefined;
      this.mgmt_vlan_def_ip_oct4 = undefined;
      this.ob_vlan_def_ip_oct1 = undefined;
      this.ob_vlan_def_ip_oct2 = undefined;
      this.ob_vlan_def_ip_oct3 = undefined;
      this.ob_vlan_def_ip_oct4 = undefined;
      if (this.play_vlan_def_ip) {
        let octetts: number[] = this.utils.ip_int_to_octetts(this.play_vlan_def_ip);
        this.play_vlan_def_ip_oct1 = octetts[0];
        this.play_vlan_def_ip_oct2 = octetts[1];
        this.play_vlan_def_ip_oct3 = octetts[2];
        this.play_vlan_def_ip_oct4 = octetts[3];
      }
      if (this.mgmt_vlan_def_ip) {
        let octetts: number[] = this.utils.ip_int_to_octetts(this.mgmt_vlan_def_ip);
        this.mgmt_vlan_def_ip_oct1 = octetts[0];
        this.mgmt_vlan_def_ip_oct2 = octetts[1];
        this.mgmt_vlan_def_ip_oct3 = octetts[2];
        this.mgmt_vlan_def_ip_oct4 = octetts[3];
      }
      if (this.ob_vlan_def_ip) {
        let octetts: number[] = this.utils.ip_int_to_octetts(this.ob_vlan_def_ip);
        this.ob_vlan_def_ip_oct1 = octetts[0];
        this.ob_vlan_def_ip_oct2 = octetts[1];
        this.ob_vlan_def_ip_oct3 = octetts[2];
        this.ob_vlan_def_ip_oct4 = octetts[3];
      }
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

  clearDevices() {
    this.rod_loading = true;
    if (this.rod) {
      this.systemService
        .execRemoveOfflineDevices()
        .subscribe({
          next: () => {
            this.refreshDevices();
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

  clearDevicesPorts() {
    this.rod_loading = true;
    if (this.rod) {
      this.deviceService
        .getDevices()
        .subscribe({
          next: (devices: Device[]) => {
            for (let i = 0; i < devices.length; i++) {
              let device: Device = devices[i];
              if (device.port_id != null) {
                this.deviceService.removePort(device.id).subscribe({next: () => {},
                  error: (err: HttpErrorResponse) => {
                    this.errorHandler.handleError(err);
                  }
                })
              }
            }
            timer(1000).subscribe(() => { this.refreshDevices() });
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

  clearDevicesWoDesc() {
    this.rod_loading = true;
    if (this.rod) {
      this.deviceService
        .getDevices()
        .subscribe({
          next: (devices: Device[]) => {
            for (let i = 0; i < devices.length; i++) {
              let device: Device = devices[i];
              if (device.desc == '') {
                this.deviceService.deleteDevice(device.id).subscribe({next: () => {},
                  error: (err: HttpErrorResponse) => {
                    this.errorHandler.handleError(err);
                  }
                })
              }
            }
            timer(1000).subscribe(() => { this.refreshDevices() });
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

  save_settings() {
    if (this.settings) {
      for (let s of this.settings_rw) {
        this.settingService
          .updateSetting(s.id, s.value)
          .subscribe({
            next: () => {},
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
    }
  }

  save_settingsPlayNw() {
    if (this.settings_play_nw) {
      for (let s of this.settings_play_nw) {
        this.settingService
          .updateSetting(s.id, s.value)
          .subscribe({
            next: () => {},
            error: (err: HttpErrorResponse) => {
              this.errorHandler.handleError(err);
            }
          })
      }
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
                        if (this.sso_ip_overwrite_enabled == false || this.sso_ip_overwrite == '') this.sso_ip_overwrite = null;
                        this.settingService
                          .updateSetting("sso_ip_overwrite", this.sso_ip_overwrite)
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

  save_vlan_def_ips() {
    if (this.vlan_def_ips) {
      if (!this.play_vlan_def_ip_saved && this.play_vlan_def_ip_oct1 != undefined && this.play_vlan_def_ip_oct2 != undefined && this.play_vlan_def_ip_oct3 != undefined && this.play_vlan_def_ip_oct4 != undefined) {
        let ip: number = this.utils.ip_octetts_to_int([this.play_vlan_def_ip_oct1, this.play_vlan_def_ip_oct2, this.play_vlan_def_ip_oct3, this.play_vlan_def_ip_oct4]);
        this.settingService.updateSetting('play_vlan_def_ip', ip).subscribe({
          next: () => {
            this.play_vlan_def_ip = ip;
            this.play_vlan_def_ip_saved = true;
          }
        });
        this.settingService.updateSetting('play_vlan_def_mask', this.play_vlan_def_mask).subscribe();
      }
      if (!this.mgmt_vlan_def_ip_saved && this.mgmt_vlan_def_ip_oct1 != undefined && this.mgmt_vlan_def_ip_oct2 != undefined && this.mgmt_vlan_def_ip_oct3 != undefined && this.mgmt_vlan_def_ip_oct4 != undefined) {
        let ip: number = this.utils.ip_octetts_to_int([this.mgmt_vlan_def_ip_oct1, this.mgmt_vlan_def_ip_oct2, this.mgmt_vlan_def_ip_oct3, this.mgmt_vlan_def_ip_oct4]);
        this.settingService.updateSetting('mgmt_vlan_def_ip', ip).subscribe({
          next: () => {
            this.mgmt_vlan_def_ip = ip;
            this.mgmt_vlan_def_ip_saved = true;
          }
        });
        this.settingService.updateSetting('mgmt_vlan_def_mask', this.mgmt_vlan_def_mask).subscribe();
      }
      if (!this.ob_vlan_def_ip_saved && this.ob_vlan_def_ip_oct1 != undefined && this.ob_vlan_def_ip_oct2 != undefined && this.ob_vlan_def_ip_oct3 != undefined && this.ob_vlan_def_ip_oct4 != undefined) {
        let ip: number = this.utils.ip_octetts_to_int([this.ob_vlan_def_ip_oct1, this.ob_vlan_def_ip_oct2, this.ob_vlan_def_ip_oct3, this.ob_vlan_def_ip_oct4]);
        this.settingService.updateSetting('ob_vlan_def_ip', ip).subscribe({
          next: () => {
            this.ob_vlan_def_ip = ip;
            this.ob_vlan_def_ip_saved = true;
          }
        });
        this.settingService.updateSetting('ob_vlan_def_mask', this.ob_vlan_def_mask).subscribe();
      }
    }
  }

}
