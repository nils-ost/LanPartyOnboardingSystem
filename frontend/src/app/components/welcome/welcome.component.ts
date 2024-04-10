import { Component, OnChanges, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Login } from 'src/app/interfaces/login';
import { Onboarding } from 'src/app/interfaces/onboarding';
import { System } from 'src/app/interfaces/system';
import { LoginService } from 'src/app/services/login.service';
import { SystemService } from 'src/app/services/system.service';

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent implements OnInit, OnChanges {
  uri: String = window.location.pathname;
  login: boolean = false;
  onboarding?: Onboarding;
  system?: System;

  constructor(
    private loginService: LoginService,
    private systemService: SystemService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.refreshSystem();
    this.refreshLogin();
  }

  ngOnChanges(): void {
    this.refreshSystem();
    this.refreshLogin();
  }

  refreshLogin() {
    this.loginService
      .getLogin()
      .subscribe(
        (login: Login) => {
          if (login.complete) this.login = true;
          else this.login = false;
        }
      )
  }

  refreshSystem() {
    this.systemService
      .getSystem()
      .subscribe(
        (system: System) => {
          this.system = system;
        }
      )
  }

  onboardingChanged(newOnboarding: Onboarding | undefined) {
    this.onboarding = newOnboarding;
  }

  gotoLogin() {
    this.router.navigate(['/login']);
  }

  gotoDE() {
    window.location.href = '/de/';
  }

  gotoEN() {
    window.location.href = '/en/';
  }

}
