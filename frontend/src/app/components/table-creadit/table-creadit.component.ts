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
    this.ippoolsOptions = list;
  }

  refreshSwitchesOptions() {
    let list: any[] = [];
    for (let i = 0; i < this.switches.length; i++) {
      let sw: Switch = this.switches[i];
      if (sw.purpose = SwitchPurposeType.mixed || sw.purpose == SwitchPurposeType.participants)
        list.push({name: sw.addr, code: sw.id});
    }
    this.switchesOptions = list;
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

  fillErrors(errors: any) {}
}
