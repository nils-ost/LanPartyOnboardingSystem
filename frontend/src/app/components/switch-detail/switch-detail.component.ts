import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Port } from 'src/app/interfaces/port';
import { Switch, SwitchPurposeType } from 'src/app/interfaces/switch';
import { Vlan } from 'src/app/interfaces/vlan';

@Component({
  selector: 'app-switch-detail',
  templateUrl: './switch-detail.component.html',
  styleUrls: ['./switch-detail.component.scss']
})
export class SwitchDetailComponent {
  @Input() selectedSwitch!: Switch;
  @Input() switches!: Switch[];
  @Input() vlans!: Vlan[];
  @Input() ports!: Port[];
  @Input() vlansNames: Map<string, string> = new Map<string, string>;
  @Output() editedSwitchEvent = new EventEmitter<null>();
  switchPurposeType = SwitchPurposeType;

  editedSwitch() {
    this.editedSwitchEvent.emit(null);
  }
}
