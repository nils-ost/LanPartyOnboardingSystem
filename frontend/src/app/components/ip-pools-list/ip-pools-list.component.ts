import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { UtilsService } from 'src/app/services/utils.service';

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
    private ippoolService: IpPoolService,
    public utils: UtilsService
  ) {}

  ngOnChanges(): void {
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansNames.set(vlan.id, vlan.number + ': ' + vlan.desc);
    }
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
