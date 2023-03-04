import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, OnChanges } from '@angular/core';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { IpPoolService } from 'src/app/services/ip-pool.service';

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
  vlansOptions: any[];

  range_start_oct1: number;
  range_start_oct2: number;
  range_start_oct3: number;
  range_start_oct4: number;
  range_end_oct1: number;
  range_end_oct2: number;
  range_end_oct3: number;
  range_end_oct4: number;

  constructor(
    private errorHandler: ErrorHandlerService,
    private ippoolService: IpPoolService
  ) {
    this.vlansOptions = [];
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

  ngOnChanges(): void {
    if (this.ippool) {
      this.desc = this.ippool.desc;
      this.mask = this.ippool.mask;
      this.range_start = this.ippool.range_start;
      this.range_end = this.ippool.range_end;
      this.vlan_id = this.ippool.vlan_id;
    }
    this.clearErrors();
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

  refreshVlansOptions() {
    let list = [{name: '', code: null}];
    for (let i = 0; i < this.vlans.length; i++) {
      let vlan: Vlan = this.vlans[i];
      let element: any = {
        name: vlan.number + ': ' + vlan.desc,
        code: vlan.id
      };
      list.push(element);
    }
    this.vlansOptions = list;
  }

  commitIpPool() {
    if (this.ippool) this.editIpPool();
    else this.createIpPool();
  }

  createIpPool() {
    this.clearErrors();
    this.ippoolService
      .createIpPool(this.desc, this.mask, this.range_start, this.range_end, this.vlan_id)
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
      .updateIpPool(this.ippool!.id, this.desc, this.mask, this.range_start, this.range_end, this.vlan_id)
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

  clearErrors() {}

  fillErrors(errors: any) {}

}
