import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { VlanService } from 'src/app/services/vlan.service';

@Component({
  selector: 'app-vlan-creadit',
  templateUrl: './vlan-creadit.component.html',
  styleUrls: ['./vlan-creadit.component.scss']
})
export class VlanCreaditComponent implements OnChanges {
  @Input() vlan?: Vlan;
  @Output() dialogEndEvent = new EventEmitter<null>();
  number!: number;
  purpose: number = 2;
  desc: string = "";
  number_error?: string;
  purpose_error?: string;
  purposes: any[];

  constructor(
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService
  ) {
    this.purposes = [
      {name: "play", code: 0},
      {name: "mgmt", code: 1},
      {name: "onboarding", code: 2},
      {name: "other", code: 3}
    ]
  }
  ngOnChanges(changes: SimpleChanges): void {
    if (this.vlan) {
      this.number = this.vlan.number;
      this.purpose = this.vlan.purpose;
      this.desc = this.vlan.desc;
    }
    this.clearErrors();
  }

  commitVlan() {
    if (this.vlan) this.editVlan();
    else this.createVlan();
  }

  createVlan() {
    this.clearErrors();
    this.vlanService
      .createVlan(this.number, this.purpose, this.desc)
      .subscribe({
        next: (vlan: Vlan) => {
          this.dialogEndEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.fillErrors(this.errorHandler.elementErrors);
        }
      })
  }

  editVlan() {
    this.clearErrors();
    this.vlanService
      .updateVlan(this.vlan!.id, this.number, this.purpose, this.desc)
      .subscribe({
        next: (vlan: Vlan) => {
          this.dialogEndEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          if (this.errorHandler.elementError) this.fillErrors(this.errorHandler.elementErrors);
        }
      })
  }

  clearErrors() {
    this.number_error = undefined;
    this.purpose_error = undefined;
  }

  fillErrors(errors: any) {
    if (errors.number) {
      if (errors.number.code === 1) this.number_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.number.code === 2) this.number_error = $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`;
      if (errors.number.code === 3) this.number_error = $localize `:@@ElementErrorCode3:invalid type`;
      if (errors.number.code === 10) this.number_error = $localize `:@@ElementErrorCode10:needs to be in range of 1 to 1024`;
    }
    if (errors.purpose) {
      if (errors.purpose.code === 3) this.purpose_error = $localize `:@@ElementErrorCode3:invalid type`;
      if (errors.purpose.code === 11) this.purpose_error = $localize `:@@ElementErrorCode11:invalid selection`;
      if (errors.purpose.code === 12) this.purpose_error = $localize `:@@ElementErrorCode12:allready in use, can only be used once`;
    }
  }
}
