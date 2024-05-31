import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { System } from 'src/app/interfaces/system';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SystemService } from 'src/app/services/system.service';

@Component({
  selector: 'app-settings-screen',
  templateUrl: './settings-screen.component.html',
  styleUrls: ['./settings-screen.component.scss']
})
export class SettingsScreenComponent implements OnInit {
  system?: System;
  nlpt_sso_enabled: boolean = false;

  constructor(
    private errorHandler: ErrorHandlerService,
    private systemService: SystemService
  ) {}

  ngOnInit(): void {
    this.refreshSystem();
  }

  refreshSystem() {
    this.systemService
      .getSystem()
      .subscribe({
        next: (system: System) => {
          this.system = system;
          this.nlpt_sso_enabled = system.nlpt_sso;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  save() {
    if(this.system?.nlpt_sso != this.nlpt_sso_enabled) {
      this.systemService
        .setNlptSso(this.nlpt_sso_enabled)
        .subscribe({
          next: () => {
            this.refreshSystem();
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
  }

}
