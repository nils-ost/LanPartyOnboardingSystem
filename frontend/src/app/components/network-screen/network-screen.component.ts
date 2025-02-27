import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { ErrorHandlerService } from '../../services/error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { MessageService } from 'primeng/api';
import { Subscription, timer, Subject } from 'rxjs';
import { Vlan } from '../../interfaces/vlan';
import { VlanService } from '../../services/vlan.service';
import { Switch } from 'src/app/interfaces/switch';
import { SwitchService } from 'src/app/services/switch.service';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { Port } from 'src/app/interfaces/port';
import { PortService } from 'src/app/services/port.service';
import { SystemService } from 'src/app/services/system.service';

@Component({
  selector: 'app-network-screen',
  templateUrl: './network-screen.component.html',
  styleUrls: ['./network-screen.component.scss']
})
export class NetworkScreenComponent implements OnInit, OnDestroy {
  @ViewChild('createvlan') createVlanDialog: any;
  @ViewChild('createswitch') createSwitchDialog: any;
  @ViewChild('createippool') createIpPoolDialog: any;
  refreshPortsTimer = timer(20000, 20000);
  refreshPortsTimerSubscription: Subscription | undefined;
  vlans: Vlan[] = [];
  switches: Switch[] = [];
  ippools: IpPool[] = [];
  ports: Port[] = [];
  commit_all: boolean = false;
  retreat_all: boolean = false;

  constructor(
    private errorHandler: ErrorHandlerService,
    private messageService: MessageService,
    private vlanService: VlanService,
    private switchService: SwitchService,
    private ippoolService: IpPoolService,
    private portService: PortService,
    private systemService: SystemService
  ) { }

  ngOnInit(): void {
    this.refreshVlans();
    this.refreshSwitches();
    this.refreshIpPools();
    this.refreshPorts();
    this.enableAutoRefresh();
  }

  ngOnDestroy(): void {
    this.disableAutoRefresh();
  }

  enableAutoRefresh() {
    this.refreshPortsTimerSubscription = this.refreshPortsTimer.subscribe(() => this.refreshPorts());
  }

  disableAutoRefresh() {
    this.refreshPortsTimerSubscription?.unsubscribe();
  }

  refreshVlans() {
    this.vlanService
      .getVlans()
      .subscribe({
        next: (vlans: Vlan[]) => {
          this.vlans = vlans;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshSwitches() {
    this.switchService
      .getSwitches()
      .subscribe({
        next: (switches: Switch[]) => {
          this.switches = switches;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshIpPools() {
    this.ippoolService
      .getIpPools()
      .subscribe({
        next: (ippools: IpPool[]) => {
          this.ippools = ippools;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  refreshPorts() {
    this.portService
      .getPorts()
      .subscribe({
        next: (ports: Port[]) => {
          this.ports = ports;
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

  creaditVlan() {
    this.createVlanDialog.hide();
    this.refreshVlans();
  }

  creaditSwitch() {
    this.createSwitchDialog.hide();
    this.refreshSwitches();
    this.refreshVlans();
    this.refreshPorts();
  }

  creaditIpPool() {
    this.createIpPoolDialog.hide();
    this.refreshIpPools();
  }

  doCheckIntegrity() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemCheckIntegrityStartedSummary:checking integrity`,
      detail: $localize `:@@SystemCheckIntegrityStartedDetail:checking system integrity started`,
      life: 6000
    });
    this.systemService
      .checkIntegrity()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemCheckIntegritySuccessSummary:Done`,
            detail: $localize `:@@SystemCheckIntegritySuccessDetail:system integrity is valid`,
            life: 6000
          });
          if (this.commit_all) this.doHaproxyCommit();
          if (this.retreat_all) this.doDhcpServersRetreat();
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
          let detail: string = 'unknown';
          if (this.errorHandler.elementError) {
            detail = this.errorHandler.elementErrors.desc;
          }
          this.messageService.add({
            severity: 'error',
            summary: $localize `:@@SystemCheckIntegrityErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doSystemCommit() {
    this.commit_all = true;
    this.doCheckIntegrity();
  }

  doHaproxyCommit() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecCommitStartedSummary:Commiting`,
      detail: $localize `:@@SystemExecCommitHaproxyStartedDetail:commiting of HAproxy settings started`,
      life: 6000
    });
    this.systemService
      .execCommitHaproxy()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecCommitSuccessSummary:Done`,
            detail: $localize `:@@SystemExecCommitHaproxySuccessDetail:HAproxy settings successful commited`,
            life: 6000
          });
          if (this.commit_all) this.doSwitchesCommit();
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

  doSwitchesCommit() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecCommitStartedSummary:Commiting`,
      detail: $localize `:@@SystemExecCommitSwitchesStartedDetail:commiting of all Switches started`,
      life: 6000
    });
    this.systemService
      .execCommitSwitches()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecCommitSuccessSummary:Done`,
            detail: $localize `:@@SystemExecCommitSwitchesSuccessDetail:all Switches successful commited`,
            life: 6000
          });
          if (this.commit_all) this.doInterfacesCommit();
          this.refreshSwitches();
          this.refreshPorts();
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

  doInterfacesCommit() {
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
          if (this.commit_all) this.doDnsServerCommit();
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

  doDnsServerCommit() {
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
          if (this.commit_all) this.doDhcpServerCommit();
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

  doDhcpServerCommit() {
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
          this.commit_all = false;
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

  doSystemRetreat() {
    this.retreat_all = true;
    this.doCheckIntegrity();
  }

  doSwitchesRetreat() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecRetreatStartedSummary:Retreating`,
      detail: $localize `:@@SystemExecRetreatSwitchesStartedDetail:retreating of all Switches started`,
      life: 6000
    });
    this.systemService
      .execRetreatSwitches()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecRetreatSuccessSummary:Done`,
            detail: $localize `:@@SystemExecRetreatSwitchesSuccessDetail:all Switches successful retreated`,
            life: 6000
          });
          this.retreat_all = false;
          this.refreshSwitches();
          this.refreshPorts();
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
            summary: $localize `:@@SystemExecRetreatErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doInterfacesRetreat() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecRetreatStartedSummary:Retreating`,
      detail: $localize `:@@SystemExecRetreatInterfacesStartedDetail:retreating of all OS-VLAN-Interfaces started`,
      life: 6000
    });
    this.systemService
      .execRetreatInterfaces()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecRetreatSuccessSummary:Done`,
            detail: $localize `:@@SystemExecRetreatInterfacesSuccessDetail:all OS-VLAN-Interfaces successful retreated`,
            life: 6000
          });
          if (this.retreat_all) this.doSwitchesRetreat();
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
            summary: $localize `:@@SystemExecRetreatErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doDnsServersRetreat() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecRetreatStartedSummary:Retreating`,
      detail: $localize `:@@SystemExecRetreatDnsServersStartedDetail:retreating of all DNS servers started`,
      life: 6000
    });
    this.systemService
      .execRetreatDnsServers()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecRetreatSuccessSummary:Done`,
            detail: $localize `:@@SystemExecRetreatDnsServersSuccessDetail:all DNS servers successful retreated`,
            life: 6000
          });
          if (this.retreat_all) this.doInterfacesRetreat();
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
            summary: $localize `:@@SystemExecRetreatErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

  doDhcpServersRetreat() {
    this.messageService.add({
      severity: 'info',
      summary: $localize `:@@SystemExecRetreatStartedSummary:Retreating`,
      detail: $localize `:@@SystemExecRetreatDhcpServersStartedDetail:retreating of all DHCP servers started`,
      life: 6000
    });
    this.systemService
      .execRetreatDhcpServers()
      .subscribe({
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: $localize `:@@SystemExecRetreatSuccessSummary:Done`,
            detail: $localize `:@@SystemExecRetreatDhcpServersSuccessDetail:all DHCP servers successful retreated`,
            life: 6000
          });
          if (this.retreat_all) this.doDnsServersRetreat();
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
            summary: $localize `:@@SystemExecRetreatErrorSummary:Error`,
            detail: detail,
            life: 6000
          });
        }
      })
  }

}
