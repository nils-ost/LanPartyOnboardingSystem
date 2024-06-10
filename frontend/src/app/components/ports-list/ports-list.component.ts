import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { Port, PortCommitConfig } from 'src/app/interfaces/port';
import { Switch } from 'src/app/interfaces/switch';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { PortService } from 'src/app/services/port.service';

@Component({
  selector: 'app-ports-list',
  templateUrl: './ports-list.component.html',
  styleUrls: ['./ports-list.component.scss']
})
export class PortsListComponent implements OnChanges, OnInit {
  @Input() ports: Port[] = [];
  @Input() vlans: Vlan[] = [];
  @Input() switches: Switch[] = [];
  @Input() selectedSwitch?: Switch;
  @Output() editedPortEvent = new EventEmitter<null>();

  @ViewChild('editdesc') editDescDialog: any;
  @ViewChild('editswitchlinkportid') editSwitchlinkPortIdDialog: any;
  editVlanConfigDialog: boolean = false;

  vlansNames: Map<string, string> = new Map<string, string>;
  vlansSelectable: any[] = [];
  displayPorts: Port[] =[];
  selectedPort: Port | undefined;
  selectedPortName: string = "";
  newDesc: string = "";
  newSwitchlinkPortId: string | null = null;
  switchlinkOptions: any[];
  vlanModeOptions: any[] = [{name: 'disabled', code: '0x00'}, {name: 'optional', code: '0x01'}, {name: 'enabled', code: '0x02'}, {name: 'strict', code: '0x03'}];
  vlanReceiveOptions: any[] = [{name: 'any', code: '0x00'}, {name: 'only tagged', code: '0x01'}, {name: 'only untagged', code: '0x02'}];

  vlan_commit_setting: string = "auto";
  vlan_commit_config!: PortCommitConfig;
  vlan_retreat_setting: string = "auto";
  vlan_retreat_config!: PortCommitConfig;

  constructor(
    private errorHandler: ErrorHandlerService,
    private portService: PortService
  ) {
    this.switchlinkOptions = [{name: 'None', code: null}];
  }

  ngOnInit(): void {
    this.refreshVlanNames();
    this.refreshDisplay();
    this.refreshSwitchlinkOptions();
  }

  ngOnChanges(): void {
    this.refreshVlanNames();
    this.refreshDisplay();
    this.refreshSwitchlinkOptions();
  }

  refreshSwitchlinkOptions() {
    let list: any[] = [{name: 'None', code: null}];
    for (let i = 0; i < this.ports.length; i++) {
      let port: Port = this.ports[i];
      if (port.switchlink) {
        let element: any = {
          name: this.switchAddrById(port.switch_id) + ' (' + this.switchDescById(port.switch_id) + '): ' + port.number,
          code: port.id
        };
        list.push(element);
      }
    }
    this.switchlinkOptions = list;
  }

  refreshDisplay() {
    if (this.selectedSwitch) {
      let newList: Port[] = [];
      for (let i = 0; i < this.ports.length; i++) {
        let port: Port = this.ports[i];
        if (port.switch_id === this.selectedSwitch.id) newList.push(port);
      }
      this.displayPorts = newList;
    }
    else this.displayPorts = this.ports;
  }

  refreshVlanNames() {
    let selectables: any[] = [];
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansNames.set(vlan.id, vlan.number + ': ' + vlan.desc);
      selectables.push({'label': vlan.number + ': ' + vlan.desc, 'value': vlan.id})
    }
    this.vlansSelectable = selectables;
  }

  editDescStart(port: Port, event: any) {
    this.selectedPort = port;
    this.newDesc = port.desc;
    this.editDescDialog.show(event);
  }

  editDesc() {
    if (this.selectedPort) {
      this.portService
        .updateDesc(this.selectedPort.id, this.newDesc)
        .subscribe({
          next: (response: any) => {
            this.editedPortEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedPort = undefined;
    this.editDescDialog.hide();
  }

  editSwitchlinkPortIdStart(port: Port, event: any) {
    this.selectedPort = port;
    this.newSwitchlinkPortId = port.switchlink_port_id;
    this.editSwitchlinkPortIdDialog.show(event);
  }

  editSwitchlinkPortId() {
    if (this.selectedPort) {
      this.portService
        .updateSwitchlinkPortId(this.selectedPort.id, this.newSwitchlinkPortId)
        .subscribe({
          next: (response: any) => {
            this.editedPortEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedPort = undefined;
    this.editSwitchlinkPortIdDialog.hide();
  }

  editParticipants(port: Port, newValue: boolean) {
    this.portService
      .updateParticipants(port.id, newValue)
      .subscribe({
        next: (response: any) => {
          this.editedPortEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  editVlanConfigStart(port: Port, event: any) {
    this.selectedPort = port;
    if (this.selectedSwitch) this.selectedPortName = this.selectedSwitch.desc + ": " + port.number;
    this.vlan_commit_config = {
      vlans: [],
      default: "",
      enabled: true,
      mode: "0x01",
      receive: "0x00",
      force: false
    } as PortCommitConfig;
    if (port.commit_disabled) this.vlan_commit_setting = "disable";
    else if (port.commit_config) {
      this.vlan_commit_setting = "manual";
      this.vlan_commit_config = port.commit_config;
    }
    else this.vlan_commit_setting = "auto";
    this.vlan_retreat_config = {
      vlans: [],
      default: "",
      enabled: true,
      mode: "0x01",
      receive: "0x00",
      force: false
    } as PortCommitConfig;
    if (port.retreat_disabled) this.vlan_retreat_setting = "disable";
    else if (port.retreat_config) {
      this.vlan_retreat_setting = "manual";
      this.vlan_retreat_config = port.retreat_config;
    }
    else this.vlan_retreat_setting = "auto";
    this.editVlanConfigDialog = true;
  }

  editVlanConfigAbort() {
    this.selectedPort = undefined;
    this.selectedPortName = "";
  }

  editVlanConfig() {
    if (this.selectedPort) {
      let commit_disabled: boolean = false;
      let commit_config: any = this.vlan_commit_config;
      if (this.vlan_commit_setting != 'manual') commit_config = null;
      if (this.vlan_commit_setting == 'disable') commit_disabled = true;
      let retreat_disabled: boolean = false;
      let retreat_config: any = this.vlan_retreat_config;
      if (this.vlan_retreat_setting != 'manual') retreat_config = null;
      if (this.vlan_retreat_setting == 'disable') retreat_disabled = true;
      this.portService
        .updateCommitConfig(this.selectedPort.id, commit_config, retreat_config, commit_disabled, retreat_disabled)
        .subscribe({
          next: () => {
            this.editedPortEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedPort = undefined;
    this.editVlanConfigDialog = false;
  }

  editCommitDisabled(port: Port, newValue: boolean) {
    this.portService
      .updateCommitDisabled(port.id, newValue)
      .subscribe({
        next: (response: any) => {
          this.editedPortEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  switchlinkById(id: string | null) {
    for (let i = 0; i < this.switchlinkOptions.length; i++) {
      let option: any = this.switchlinkOptions[i];
      if (option.code == id) return option.name;
    }
    return '';
  }

  switchAddrById(id: string) {
    for (let i = 0; i < this.switches.length; i++) {
      let sw: Switch = this.switches[i];
      if (sw.id == id) return sw.addr;
    }
    return '';
  }

  switchDescById(id: string) {
    for (let i = 0; i < this.switches.length; i++) {
      let sw: Switch = this.switches[i];
      if (sw.id == id) return sw.desc;
    }
    return '';
  }

}
