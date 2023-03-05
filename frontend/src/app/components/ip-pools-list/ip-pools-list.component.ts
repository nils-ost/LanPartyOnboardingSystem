import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { IpPoolService } from 'src/app/services/ip-pool.service';

@Component({
  selector: 'app-ip-pools-list',
  templateUrl: './ip-pools-list.component.html',
  styleUrls: ['./ip-pools-list.component.scss']
})
export class IpPoolsListComponent implements OnChanges {
  @Input() ippools!: IpPool[];
  @Input() vlans!: Vlan[];
  @Output() editedIpPoolEvent = new EventEmitter<null>();
  vlansNames: Map<string, string> = new Map<string, string>;
  editDialog: boolean = false;
  selectedIpPool!: IpPool;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private ippoolService: IpPoolService
  ) {}

  ngOnChanges(): void {
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansNames.set(vlan.id, vlan.number + ': ' + vlan.desc);
    }
  }

  ip_int_to_str(ip: number): string {
    let result: string = "";
    let hex = ip.toString(16);
    if (hex.length < 8) hex = '0' + hex;
    result = result + parseInt(hex.slice(0, 2), 16).toString() + '.';
    result = result + parseInt(hex.slice(2, 4), 16).toString() + '.';
    result = result + parseInt(hex.slice(4, 6), 16).toString() + '.';
    result = result + parseInt(hex.slice(6, 8), 16).toString();
    return result;
  }

  editIpPool(ippool: IpPool) {
    this.selectedIpPool = ippool;
    this.editDialog = true;
  }

  editedIpPool() {
    this.editDialog = false;
    this.editedIpPoolEvent.emit(null);
  }

  confirmDelete(ippool: IpPool) {
    this.confirmationService.confirm({
        message: 'Are you sure that you want to delete IpPool ' + ippool.desc,
        accept: () => {
          this.ippoolService
            .deleteIpPool(ippool.id)
            .subscribe({
              next: (response: any) => {
                this.editedIpPoolEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
                let detail: string = $localize `:@@DeleteErrorGeneric:Unknown error`;
                if (this.errorHandler.elementError) {
                  if (this.errorHandler.elementErrors.code == 2)
                    detail = $localize `:@@DeleteErrorCode2OnIpPool:Can't delete IpPool. There is at least one Table attached to IpPool ` + ippool.desc;
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
