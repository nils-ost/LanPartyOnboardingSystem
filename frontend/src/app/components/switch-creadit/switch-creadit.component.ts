import { Component, EventEmitter, Input, Output, OnChanges } from '@angular/core';
import { Switch } from 'src/app/interfaces/switch';

@Component({
  selector: 'app-switch-creadit',
  templateUrl: './switch-creadit.component.html',
  styleUrls: ['./switch-creadit.component.scss']
})
export class SwitchCreaditComponent {
  @Input() sw?: Switch;
  @Output() dialogEndEvent = new EventEmitter<null>();
}
