import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { Device } from 'src/app/interfaces/device';
import { Port, PortCommitConfig } from 'src/app/interfaces/port';
import { Vlan, VlanPurposeType } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { PortService } from 'src/app/services/port.service';

@Component({
  selector: 'app-vlan-config-edit',
  templateUrl: './vlan-config-edit.component.html',
  styleUrls: ['./vlan-config-edit.component.scss']
})
export class VlanConfigEditComponent implements OnInit, OnChanges {
  @Input() vlans: Vlan[] = [];
  @Input() selectedPort?: Port;
  @Input() selectedDevice?: Device;
  @Output() editedPortEvent = new EventEmitter<null>();
  @Output() editedDeviceEvent = new EventEmitter<null>();

  vlanModeOptions: string[] = ['disabled', 'optional', 'enabled', 'strict'];
  vlanReceiveOptions: string[] = ['any', 'only tagged', 'only untagged'];

  vlansById: Map<string, Vlan> = new Map<string, Vlan>;
  vlansSelectable: any[] = [];
  vlansOtherSelectable: any[] = [];
  vlansCommitDefaultSelectable: any[] = [];
  vlansRetreatDefaultSelectable: any[] = [];

  vlan_commit_setting: string = "auto";
  vlan_commit_config!: PortCommitConfig;
  vlan_commit_other_vlans: string[] = [];
  vlan_retreat_setting: string = "auto";
  vlan_retreat_config!: PortCommitConfig;

  constructor(
    private errorHandler: ErrorHandlerService,
    private portService: PortService
  ) {}

  ngOnInit(): void {
    this.refreshVlanNames();
    this.prepareEdit();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ('selectedPort' in changes || 'selectedDevice' in changes) this.prepareEdit();
    if ('vlans' in changes) this.refreshVlanNames();
  }

  refreshVlanNames() {
    let selectables: any[] = [];
    let others: any[] = [];
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansById.set(vlan.id, vlan);
      selectables.push({'label': vlan.number + ': ' + vlan.desc, 'value': vlan.id})
      if (vlan.purpose == VlanPurposeType.other) others.push({'label': vlan.number + ': ' + vlan.desc, 'value': vlan.id})
    }
    this.vlansSelectable = selectables;
    this.vlansOtherSelectable = others;
  }

  commitVlansChanged() {
    let selectables: any[] = [];
    for (let vlan_id of this.vlan_commit_config.vlans) {
      let vlan: Vlan | undefined = this.vlansById.get(vlan_id);
      if (vlan) selectables.push({'label': vlan.number + ': ' + vlan.desc, 'value': vlan.id})
    }
    if (this.vlan_commit_config.default != "" && !this.vlan_commit_config.vlans.includes(this.vlan_commit_config.default)) {
      if (this.vlan_commit_config.vlans.length == 0) this.vlan_commit_config.default = "";
      else this.vlan_commit_config.default = this.vlan_commit_config.vlans[0];
    }
    this.vlansCommitDefaultSelectable = selectables;
  }

  retreatVlansChanged() {
    let selectables: any[] = [];
    for (let vlan_id of this.vlan_retreat_config.vlans) {
      let vlan: Vlan | undefined = this.vlansById.get(vlan_id);
      if (vlan) selectables.push({'label': vlan.number + ': ' + vlan.desc, 'value': vlan.id})
    }
    if (this.vlan_retreat_config.default != "" && !this.vlan_retreat_config.vlans.includes(this.vlan_retreat_config.default)) {
      if (this.vlan_retreat_config.vlans.length == 0) this.vlan_retreat_config.default = "";
      else this.vlan_retreat_config.default = this.vlan_retreat_config.vlans[0];
    }
    this.vlansRetreatDefaultSelectable = selectables;
  }

  prepareEdit() {
    // commit
    this.vlan_commit_config = {
      vlans: [],
      default: "",
      enabled: true,
      mode: "optional",
      receive: "any",
      force: false
    } as PortCommitConfig;
    this.vlan_commit_other_vlans = [];
    this.vlan_commit_setting = "auto";

    if (this.selectedPort) {
      if (this.selectedPort.commit_disabled) this.vlan_commit_setting = "disable";
      else if (this.selectedPort.commit_config) {
        this.vlan_commit_setting = "manual";
        if (this.selectedPort.switchlink) {
          if ("other_vlans" in this.selectedPort.commit_config) this.vlan_commit_other_vlans = this.selectedPort.commit_config.other_vlans;
        }
        else this.vlan_commit_config = this.selectedPort.commit_config;
      }
    }
    this.commitVlansChanged();

    // retreat
    this.vlan_retreat_config = {
      vlans: [],
      default: "",
      enabled: true,
      mode: "optional",
      receive: "any",
      force: false
    } as PortCommitConfig;
    this.vlan_retreat_setting = "auto";

    if (this.selectedPort) {
      if (this.selectedPort.retreat_disabled) this.vlan_retreat_setting = "disable";
      else if (this.selectedPort.retreat_config) {
        this.vlan_retreat_setting = "manual";
        this.vlan_retreat_config = this.selectedPort.retreat_config;
      }
    }
    this.retreatVlansChanged();
  }

  saveConfig() {
    if (this.selectedPort) {
      let commit_disabled: boolean = false;
      let commit_config: any = this.vlan_commit_config;
      if (this.selectedPort.switchlink) commit_config = {'other_vlans': this.vlan_commit_other_vlans};
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
  }
}
