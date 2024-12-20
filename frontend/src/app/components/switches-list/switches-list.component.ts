import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Port } from 'src/app/interfaces/port';
import { Switch, SwitchPurposeType } from 'src/app/interfaces/switch';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SwitchService } from 'src/app/services/switch.service';
import { SystemService } from 'src/app/services/system.service';

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
    private switchService: SwitchService,
    private systemService: SystemService
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

  commitSwitch(sw: Switch) {
    this.doInterfacesCommit(sw);
  }

  doSwitchCommit(sw: Switch) {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@CommitSwitchStartedSummary:Commiting`,
      detail: $localize `:@@CommitSwitchStartedDetail:commiting started for Switch` + ': ' + sw.addr,
      life: 6000
    });
    this.switchService
      .execCommit(sw.id)
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@CommitSwitchSuccessSummary:Done`,
            detail: $localize `:@@CommitSwitchSuccessDetail:successful commited Switch` + ': ' + sw.addr,
            life: 6000
          });
          this.editedSwitchEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@CommitSwitchErrorSummary:Error`,
            detail: $localize `:@@CommitSwitchErrorDetail:could not commit Switch` + ': ' + sw.addr,
            life: 6000
          });
        }
      })
  }

  doInterfacesCommit(sw: Switch) {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecCommitStartedSummary:Commiting`,
      detail: $localize `:@@SystemExecCommitInterfacesStartedDetail:commiting of all OS-VLAN-Interfaces started`,
      life: 6000
    });
    this.systemService
      .execCommitInterfaces()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecCommitSuccessSummary:Done`,
            detail: $localize `:@@SystemExecCommitInterfacesSuccessDetail:all OS-VLAN-Interfaces successful commited`,
            life: 6000
          });
          this.doDnsServerCommit(sw);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          let detail: string = 'unknown';
          if (this.errorHandler.elementError) {
            if (this.errorHandler.elementErrors.code == 1) detail = this.errorHandler.elementErrors.desc + ' ' + this.errorHandler.elementErrors.integrity.desc;
            else detail = this.errorHandler.elementErrors.desc;
          }
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@SystemExecCommitErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doDnsServerCommit(sw: Switch) {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecCommitStartedSummary:Commiting`,
      detail: $localize `:@@SystemExecCommitDnsServersStartedDetail:commiting of all DNS servers started`,
      life: 6000
    });
    this.systemService
      .execCommitDnsServers()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecCommitSuccessSummary:Done`,
            detail: $localize `:@@SystemExecCommitDnsServersSuccessDetail:all DNS servers successful commited`,
            life: 6000
          });
          this.doDhcpServerCommit(sw);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          let detail: string = 'unknown';
          if (this.errorHandler.elementError) {
            if (this.errorHandler.elementErrors.code == 1) detail = this.errorHandler.elementErrors.desc + ' ' + this.errorHandler.elementErrors.integrity.desc;
            else detail = this.errorHandler.elementErrors.desc;
          }
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@SystemExecCommitErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doDhcpServerCommit(sw: Switch) {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecCommitStartedSummary:Commiting`,
      detail: $localize `:@@SystemExecCommitDhcpServersStartedDetail:commiting of all DHCP servers started`,
      life: 6000
    });
    this.systemService
      .execCommitDhcpServers()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecCommitSuccessSummary:Done`,
            detail: $localize `:@@SystemExecCommitDhcpServersSuccessDetail:all DHCP servers successful commited`,
            life: 6000
          });
          this.doSwitchCommit(sw);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          let detail: string = 'unknown';
          if (this.errorHandler.elementError) {
            if (this.errorHandler.elementErrors.code == 1) detail = this.errorHandler.elementErrors.desc + ' ' + this.errorHandler.elementErrors.integrity.desc;
            else detail = this.errorHandler.elementErrors.desc;
          }
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@SystemExecCommitErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  retreatSwitch(sw: Switch) {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@RetreatSwitchStartedSummary:Retreating`,
      detail: $localize `:@@RetreatSwitchStartedDetail:retreating started for Switch` + ': ' + sw.addr,
      life: 6000
    });
    this.switchService
      .execRetreat(sw.id)
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@RetreatSwitchSuccessSummary:Done`,
            detail: $localize `:@@RetreatSwitchSuccessDetail:successful retreated Switch` + ': ' + sw.addr,
            life: 6000
          });
          this.editedSwitchEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@RetreatSwitchErrorSummary:Error`,
            detail: $localize `:@@RetreatSwitchErrorDetail:could not retreated Switch` + ': ' + sw.addr,
            life: 6000
          });
        }
      })
  }

  showPortsList(sw: Switch) {
    this.switchService
      .dummySave(sw.id)
      .subscribe({
        next: (response: any) => {
          this.editedSwitchEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
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
