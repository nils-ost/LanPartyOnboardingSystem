import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { Table } from 'src/app/interfaces/table';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Switch, SwitchPurposeType } from 'src/app/interfaces/switch';
import { Vlan, VlanPurposeType } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { TableService } from 'src/app/services/table.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-table-creadit',
  templateUrl: './table-creadit.component.html',
  styleUrls: ['./table-creadit.component.scss']
})
export class TableCreaditComponent implements OnChanges{
  @Input() table?: Table;
  @Input() vlans: Vlan[] = [];
  @Input() switches: Switch[] = [];
  @Input() ippools: IpPool[] = [];
  @Output() dialogEndEvent = new EventEmitter<null>();
  number: number = 0;
  desc: string = "";
  switch_id: string = "";
  seat_ip_pool_id: string = "";
  add_ip_pool_id: string = "";

  ippoolsOptions: any[] = [];
  switchesOptions: any[] = [];

  number_error?: string;
  switch_id_error?: string;
  seat_ip_pool_id_error?: string;
  add_ip_pool_id_error?: string;

  constructor(
    private errorHandler: ErrorHandlerService,
    private tableService: TableService
  ) {}

  ngOnChanges(): void {
    if (this.table) {
      this.number = this.table.number;
      this.desc = this.table.desc;
      this.switch_id = this.table.switch_id;
      this.seat_ip_pool_id = this.table.seat_ip_pool_id;
      this.add_ip_pool_id = this.table.add_ip_pool_id;
    }
    this.clearErrors();
    this.refreshIpPoolsOptions();
    this.refreshSwitchesOptions();
  }

  refreshIpPoolsOptions() {
    let play_vlan_id: string = "";
    for (let i = 0; i < this.vlans.length; i++) {
      if (this.vlans[i].purpose == VlanPurposeType.play) {
        play_vlan_id = this.vlans[i].id;
        break;
      }
    }
    let list: any[] = [];
    for (let i = 0; i < this.ippools.length; i++) {
      let ippool: IpPool = this.ippools[i];
      if (ippool.vlan_id == play_vlan_id)
        list.push({name: ippool.desc, code: ippool.id});
    }
    this.ippoolsOptions = list.sort((a, b) => a.name.localeCompare(b.name));
  }

  refreshSwitchesOptions() {
    let list: any[] = [];
    for (let i = 0; i < this.switches.length; i++) {
      let sw: Switch = this.switches[i];
      if (sw.purpose = SwitchPurposeType.mixed || sw.purpose == SwitchPurposeType.participants) {
        if (sw.desc != '') list.push({name: sw.desc + ' (' + sw.addr + ')', code: sw.id});
        else list.push({name: sw.addr, code: sw.id});
      }
    }
    this.switchesOptions = list.sort((a, b) => a.name.localeCompare(b.name));
  }

  commitTable() {
    if (this.table) this.editTable();
    else this.createTable();
  }

  createTable() {
    this.clearErrors();
    this.tableService
      .createTable(this.number, this.desc, this.switch_id, this.seat_ip_pool_id, this.add_ip_pool_id)
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

  editTable() {
    this.clearErrors();
    this.tableService
      .updateTable(this.table!.id, this.number, this.desc, this.switch_id, this.seat_ip_pool_id, this.add_ip_pool_id)
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
    this.number_error = undefined;
    this.switch_id_error = undefined;
    this.seat_ip_pool_id_error = undefined;
    this.add_ip_pool_id_error = undefined;
  }

  fillErrors(errors: any) {
    if (errors.number) {
      if (errors.number.code === 1) this.number_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.number.code === 2) this.number_error = $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`;
      if (errors.number.code === 3) this.number_error = $localize `:@@ElementErrorCode3:invalid type`;
      if (errors.number.code === 40) this.number_error = $localize `:@@ElementErrorCode40:needs to be bigger or equal to zero`;
    }
    if (errors.switch_id) {
      if (errors.switch_id.code === 1) this.switch_id_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.switch_id.code === 41) this.switch_id_error = $localize `:@@ElementErrorCode41:there is no Element with this ID`;
      if (errors.switch_id.code === 42) this.switch_id_error = $localize `:@@ElementErrorCode42:Purpose of Switch needs to be 1 (participants) or 2 (mixed)`;
    }
    if (errors.seat_ip_pool_id) {
      if (errors.seat_ip_pool_id.code === 1) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.seat_ip_pool_id.code === 2) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode2:value allready in use, needs to be unique`;
      if (errors.seat_ip_pool_id.code === 41) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode41:there is no Element with this ID`;
      if (errors.seat_ip_pool_id.code === 43) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode43:VLAN of IpPool needs to be of purpose 0 (play/seats)`;
      if (errors.seat_ip_pool_id.code === 44) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode44:allready in use as add_ip_pool_id on different Table`;
      if (errors.seat_ip_pool_id.code === 45) this.seat_ip_pool_id_error = $localize `:@@ElementErrorCode45:seat_ip_pool_id and add_ip_pool_id can't be the same`;
    }
    if (errors.add_ip_pool_id) {
      if (errors.add_ip_pool_id.code === 1) this.add_ip_pool_id_error = $localize `:@@ElementErrorCode1:can't be empty`;
      if (errors.add_ip_pool_id.code === 41) this.add_ip_pool_id_error = $localize `:@@ElementErrorCode41:there is no Element with this ID`;
      if (errors.add_ip_pool_id.code === 43) this.add_ip_pool_id_error = $localize `:@@ElementErrorCode43:VLAN of IpPool needs to be of purpose 0 (play/seats)`;
      if (errors.add_ip_pool_id.code === 45) this.add_ip_pool_id_error = $localize `:@@ElementErrorCode45:seat_ip_pool_id and add_ip_pool_id can't be the same`;
      if (errors.add_ip_pool_id.code === 46) this.add_ip_pool_id_error = $localize `:@@ElementErrorCode46:allready in use as seat_ip_pool_id on different Table`;
    }
  }
}
