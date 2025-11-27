import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges } from '@angular/core';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Setting } from 'src/app/interfaces/setting';
import { Vlan, VlanPurposeType } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { SettingService } from 'src/app/services/setting.service';

@Component({
  selector: 'app-ip-pool-creadit',
  templateUrl: './ip-pool-creadit.component.html',
  styleUrls: ['./ip-pool-creadit.component.scss']
})
export class IpPoolCreaditComponent implements OnChanges {
  @Input() ippool?: IpPool;
  @Input() vlans: Vlan[] = [];
  @Output() dialogEndEvent = new EventEmitter<null>();
  desc: string = "";
  mask: number = 24;
  range_start: number = 3232235521;
  range_end: number = 3232235774;
  vlan_id: string = "";
  lpos: boolean = false;
  vlansOptions: any[] = [];
  vlansToPurpose: Map<string, VlanPurposeType> = new Map<string, VlanPurposeType>;
  defaultVlanIp: Map<VlanPurposeType, number|null> = new Map<VlanPurposeType, number|null>;
  defaultVlanMask: Map<VlanPurposeType, number> = new Map<VlanPurposeType, number>;

  range_start_oct1: number = 0;
  range_start_oct2: number = 0;
  range_start_oct3: number = 0;
  range_start_oct4: number = 0;
  range_end_oct1: number = 0;
  range_end_oct2: number = 0;
  range_end_oct3: number = 0;
  range_end_oct4: number = 0;

  mask_error?: string;
  range_start_error?: string;
  range_end_error?: string;
  vlan_id_error?: string;
  lpos_error?: string;

  constructor(
    private errorHandler: ErrorHandlerService,
    private ippoolService: IpPoolService,
    private settingService: SettingService
  ) {
    this.fillRangeFields();
    this.settingService.getSettings().subscribe({
      next: (settings: Setting[]) => {
        for (let i = 0; i < settings.length; i++) {
          let setting: Setting = settings[i];
          if (setting.id == 'play_vlan_def_ip') this.defaultVlanIp.set(VlanPurposeType.play, setting.value);
          if (setting.id == 'mgmt_vlan_def_ip') this.defaultVlanIp.set(VlanPurposeType.mgmt, setting.value);
          if (setting.id == 'ob_vlan_def_ip') this.defaultVlanIp.set(VlanPurposeType.onboarding, setting.value);
          if (setting.id == 'play_vlan_def_mask') this.defaultVlanMask.set(VlanPurposeType.play, setting.value);
          if (setting.id == 'mgmt_vlan_def_mask') this.defaultVlanMask.set(VlanPurposeType.mgmt, setting.value);
          if (setting.id == 'ob_vlan_def_mask') this.defaultVlanMask.set(VlanPurposeType.onboarding, setting.value);
        }
      }
    });
  }

  ngOnChanges(): void {
    if (this.ippool) {
      this.desc = this.ippool.desc;
      this.mask = this.ippool.mask;
      this.range_start = this.ippool.range_start;
      this.range_end = this.ippool.range_end;
      this.vlan_id = this.ippool.vlan_id;
    }
    this.clearErrors();
    this.fillRangeFields();
    this.refreshVlansOptions();
  }

  int_to_octetts(addr: number): number[] {
    let list: number[] = [];
    let hex = addr.toString(16);
    if (hex.length < 8) hex = '0' + hex;
    list.push(parseInt(hex.slice(0, 2), 16));
    list.push(parseInt(hex.slice(2, 4), 16));
    list.push(parseInt(hex.slice(4, 6), 16));
    list.push(parseInt(hex.slice(6, 8), 16));
    return list;
  }

  octetts_to_int(oct: number[]): number {
    let hex = '';
    for (let i = 0; i < oct.length; i++) {
      let ohex = oct[i].toString(16);
      if (ohex.length < 2) ohex = '0' + ohex;
      hex = hex + ohex;
    }
    return parseInt(hex, 16);
  }

  fillRangeFields() {
    let range_start_octetts: number[] = this.int_to_octetts(this.range_start);
    this.range_start_oct1 = range_start_octetts[0];
    this.range_start_oct2 = range_start_octetts[1];
    this.range_start_oct3 = range_start_octetts[2];
    this.range_start_oct4 = range_start_octetts[3];
    let range_end_octetts: number[] = this.int_to_octetts(this.range_end);
    this.range_end_oct1 = range_end_octetts[0];
    this.range_end_oct2 = range_end_octetts[1];
    this.range_end_oct3 = range_end_octetts[2];
    this.range_end_oct4 = range_end_octetts[3];
  }

  refreshVlansOptions() {
    let list = [{name: '', code: null}];
    for (let i = 0; i < this.vlans.length; i++) {
      let vlan: Vlan = this.vlans[i];
      let element: any = {
        name: vlan.number + ': ' + vlan.desc,
        code: vlan.id
      };
      list.push(element);
      this.vlansToPurpose.set(vlan.id, vlan.purpose);
    }
    this.vlansOptions = list;
  }

  vlanChanged() {
    if (this.vlan_id && !this.ippool) {
      let purpose: VlanPurposeType | undefined = this.vlansToPurpose.get(this.vlan_id);
      if (purpose) {
        let ip: number | null | undefined = this.defaultVlanIp.get(purpose);
        let mask_len: number | undefined = this.defaultVlanMask.get(purpose);
        if (ip && mask_len) {
          let mask: number = (((2 ** mask_len) - 1) << (32 - mask_len)) >>>0;;
          let range_max: number  = (2 ** (32 - mask_len)) - 2;
          this.range_start = ((ip & mask) >>>0) + 1;
          this.range_end = ((ip & mask) >>>0) + range_max;
          this.mask = mask_len;
          this.fillRangeFields();
        }
      }
    }
  }

  commitIpPool() {
    this.range_start = this.octetts_to_int([this.range_start_oct1, this.range_start_oct2, this.range_start_oct3, this.range_start_oct4]);
    this.range_end = this.octetts_to_int([this.range_end_oct1, this.range_end_oct2, this.range_end_oct3, this.range_end_oct4]);
    if (this.ippool) this.editIpPool();
    else {
      let purpose: VlanPurposeType | undefined = this.vlansToPurpose.get(this.vlan_id);
      if (purpose && !this.defaultVlanIp.get(purpose)) {
        let mask: number = (((2 ** this.mask) - 1) << (32 - this.mask)) >>>0;
        let ip: number = (this.range_start & mask) >>>0;
        console.log(this.range_start);
        console.log(mask);
        console.log(ip);
        let setting: string = '';
        if (purpose.valueOf() == VlanPurposeType.play.valueOf()) setting = 'play_vlan_def_';
        if (purpose.valueOf() == VlanPurposeType.mgmt.valueOf()) setting = 'mgmt_vlan_def_';
        if (purpose.valueOf() == VlanPurposeType.onboarding.valueOf()) setting = 'ob_vlan_def_';
        this.settingService.updateSetting(setting + 'ip', ip).subscribe();
        this.settingService.updateSetting(setting + 'mask', this.mask).subscribe();
      }
      this.createIpPool()
    };
  }

  createIpPool() {
    this.clearErrors();
    this.ippoolService
      .createIpPool(this.desc, this.mask, this.range_start, this.range_end, this.vlan_id, this.lpos)
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

  editIpPool() {
    this.clearErrors();
    this.ippoolService
      .updateIpPool(this.ippool!.id, this.desc, this.mask, this.range_start, this.range_end, this.vlan_id, this.lpos)
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
    this.mask_error = undefined;
    this.range_start_error = undefined;
    this.range_end_error = undefined;
    this.vlan_id_error = undefined;
    this.lpos_error = undefined;
  }

  fillErrors(errors: any) {
    if (errors.mask) {
      if (errors.mask.code === 30) this.mask_error = $localize `:@@ElementErrorCode30:value needs to be between 8 and 30`;
      if (errors.mask.code === 31) this.mask_error = $localize `:@@ElementErrorCode31:does not fit to the IP range`;
    }
    if (errors.range_start) {
      if (errors.range_start.code === 32) this.range_start_error = $localize `:@@ElementErrorCode32:range_start needs to be smaller than range_end`;
      if (errors.range_start.code === 33) this.range_start_error = $localize `:@@ElementErrorCode33:overlaps with existing IpPool`;
      if (errors.range_start.code === 34) this.range_start_error = $localize `:@@ElementErrorCode34:not a valid IP`;
      if (errors.range_start.code === 38) this.range_start_error = $localize `:@@ElementErrorCode38:range_start and range_end need to be equal`;
    }
    if (errors.range_end) {
      if (errors.range_end.code === 32) this.range_end_error = $localize `:@@ElementErrorCode32:range_start needs to be smaller than range_end`;
      if (errors.range_end.code === 33) this.range_end_error = $localize `:@@ElementErrorCode33:overlaps with existing IpPool`;
      if (errors.range_end.code === 34) this.range_end_error = $localize `:@@ElementErrorCode34:not a valid IP`;
      if (errors.range_end.code === 38) this.range_end_error = $localize `:@@ElementErrorCode38:range_start and range_end need to be equal`;
    }
    if (errors.vlan_id) {
      if (errors.vlan_id.code === 1) this.vlan_id_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.vlan_id.code === 35) this.vlan_id_error = $localize `:@@ElementErrorCode35:there is no VLAN with this ID`;
      if (errors.vlan_id.code === 37) this.vlan_id_error = $localize `:@@ElementErrorCode37:Purpose of VLAN needs to be 0 (play)`;
      if (errors.vlan_id.code === 39) this.vlan_id_error = $localize `:@@ElementErrorCode39:only one IpPool per VLAN with this purpose is allowed`;
    }
    if (errors.lpos) {
      if (errors.lpos.code === 36) this.lpos_error = $localize `:@@ElementErrorCode36:Only allowed once, but there is already an IpPool set as LPOS`;
    }
  }

}
