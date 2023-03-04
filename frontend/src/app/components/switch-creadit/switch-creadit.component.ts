import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges, OnInit } from '@angular/core';
import { Switch } from 'src/app/interfaces/switch';
import { Vlan, VlanPurposeType } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SwitchService } from 'src/app/services/switch.service';

@Component({
  selector: 'app-switch-creadit',
  templateUrl: './switch-creadit.component.html',
  styleUrls: ['./switch-creadit.component.scss']
})
export class SwitchCreaditComponent implements OnChanges, OnInit {
  @Input() sw?: Switch;
  @Input() vlans: Vlan[] = [];
  @Output() dialogEndEvent = new EventEmitter<null>();
  addr: string = "";
  user: string = "";
  pw: string = "";
  purpose: number = 1;
  onboarding_vlan_id: string | null = null;
  addr_error?: string;
  purpose_error?: string;
  onboarding_vlan_id_error?: string;
  purposes: any[];
  vlansOptions: any[];

  constructor(
    private errorHandler: ErrorHandlerService,
    private switchService: SwitchService
  ) {
    this.purposes = [
      {name: "core", code: 0},
      {name: "participants", code: 1},
      {name: "mixed", code: 2}
    ]
    this.vlansOptions = [{name: '', code: null}];
  }

  ngOnInit(): void {
  }

  ngOnChanges(): void {
    if (this.sw) {
      this.addr = this.sw.addr;
      this.user = this.sw.user;
      this.pw = this.sw.pw;
      this.purpose = this.sw.purpose;
      this.onboarding_vlan_id = this.sw.onboarding_vlan_id;
    }
    this.clearErrors();
    this.refreshVlansOptions();
  }

  refreshVlansOptions() {
    let list = [{name: '', code: null}];
    for (let i = 0; i < this.vlans.length; i++) {
      let vlan: Vlan = this.vlans[i];
      if (vlan.purpose == VlanPurposeType.onboarding) {
        let element: any = {
          name: vlan.number + ': ' + vlan.desc,
          code: vlan.id
        };
        list.push(element);
      }
    }
    this.vlansOptions = list;
  }

  commitSwitch() {
    if (this.sw) this.editSwitch();
    else this.createSwitch();
  }

  createSwitch() {
    this.clearErrors();
    this.switchService
      .createSwitch(this.addr, this.user, this.pw, this.purpose, this.onboarding_vlan_id)
      .subscribe({
        next: (response: any) => {
          this.dialogEndEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.fillErrors(this.errorHandler.elementErrors);
        }
      })
  }

  editSwitch() {
    this.clearErrors();
    this.switchService
      .updateSwitch(this.sw!.id, this.addr, this.user, this.pw, this.purpose, this.onboarding_vlan_id)
      .subscribe({
        next: (response: any) => {
          this.dialogEndEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.fillErrors(this.errorHandler.elementErrors);
        }
      })
  }

  clearErrors() {
    this.onboarding_vlan_id_error = undefined;
    this.purpose_error = undefined;
    this.addr_error = undefined;
  }

  fillErrors(errors: any) {
    if (errors.addr) {
      if (errors.addr.code === 2) this.addr_error = $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`;
    }
    if (errors.purpose) {
      if (errors.purpose.code === 1) this.purpose_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.purpose.code === 3) this.purpose_error = $localize `:@@ElementErrorCode3:invalid type`;
      if (errors.purpose.code === 20) this.purpose_error = $localize `:@@ElementErrorCode20:invalid purpose`;
    }
    if (errors.onboarding_vlan_id) {
      if (errors.onboarding_vlan_id.code === 1) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.onboarding_vlan_id.code === 3) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode3:invalid type`;
      if (errors.onboarding_vlan_id.code === 21) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode21:can't be empty for given purpose`;
      if (errors.onboarding_vlan_id.code === 22) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode22:there is no VLAN with this ID`;
      if (errors.onboarding_vlan_id.code === 23) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode23:this VLAN is not of purpose Onboarding`;
      if (errors.onboarding_vlan_id.code === 24) this.onboarding_vlan_id_error = $localize `:@@ElementErrorCode24:this VLAN is allready used on a different Switch`;
    }
  }
}
