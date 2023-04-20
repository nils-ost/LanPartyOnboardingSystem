import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Port } from 'src/app/interfaces/port';
import { Switch, SwitchPurposeType } from 'src/app/interfaces/switch';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SwitchService } from 'src/app/services/switch.service';

@Component({
  selector: 'app-switches-list',
  templateUrl: './switches-list.component.html',
  styleUrls: ['./switches-list.component.scss']
})
export class SwitchesListComponent implements OnChanges {
  switchPurposeType = SwitchPurposeType;
  @Input() switches!: Switch[];
  @Input() vlans!: Vlan[];
  @Input() ports: Port[] = [];
  @Output() editedSwitchEvent = new EventEmitter<null>();
  vlansNames: Map<string, string> = new Map<string, string>;
  editDialog: boolean = false;
  portsListDialog: boolean = false;
  selectedSwitch!: Switch;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private switchService: SwitchService
  ) {}

  ngOnChanges(): void {
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansNames.set(vlan.id, vlan.number + ': ' + vlan.desc);
    }
  }

  portCount(switch_id: string, participants: boolean = false): number {
    if (participants)
      return this.ports.filter((port) => port.switch_id === switch_id && port.participants == true).length;
    else
      return this.ports.filter((port) => port.switch_id === switch_id).length;
  }

  editSwitch(sw: Switch) {
    this.selectedSwitch = sw;
    this.editDialog = true;
  }

  editedSwitch() {
    this.editDialog = false;
    this.editedSwitchEvent.emit(null);
  }

  showPortsList(sw: Switch) {
    this.selectedSwitch = sw;
    this.portsListDialog = true;
  }

  confirmDelete(sw: Switch) {
    this.confirmationService.confirm({
        message: 'Are you sure that you want to delete Switch ' + sw.addr,
        accept: () => {
          this.switchService
            .deleteSwitch(sw.id)
            .subscribe({
              next: (response: any) => {
                this.editedSwitchEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
                let detail: string = $localize `:@@DeleteErrorGeneric:Unknown error`;
                if (this.errorHandler.elementError) {
                  if (this.errorHandler.elementErrors.code == 2)
                    detail = $localize `:@@DeleteErrorCode2OnSwitch:Can't delete Switch. There is at least one Table attached to Switch ` + sw.addr;
                }
                this.messageService.add({
                  severity: 'error',
                  summary: $localize `:@@DeleteErrorSummary:deletion not possible`,
                  detail: detail,
                  life: 6000
                });
              }
            })
        }
    });
  }
}
