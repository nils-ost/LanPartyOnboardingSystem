import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Vlan, VlanPurposeType } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { VlanService } from 'src/app/services/vlan.service';

@Component({
  selector: 'app-vlans-list',
  templateUrl: './vlans-list.component.html',
  styleUrls: ['./vlans-list.component.scss']
})
export class VlansListComponent {
  vlanPurposeType = VlanPurposeType;
  @Input() vlans!: Vlan[];
  @Output() editedVlanEvent = new EventEmitter<null>();
  editDialog: boolean = false;
  selectedVlan!: Vlan;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService
  ) {}

  editVlan(vlan: Vlan) {
    this.selectedVlan = vlan;
    this.editDialog = true;
  }

  editedVlan() {
    this.editDialog = false;
    this.editedVlanEvent.emit(null);
  }

  confirmDelete(vlan: Vlan) {
    this.confirmationService.confirm({
        message: 'Are you sure that you want to delete VLAN ' + vlan.number,
        accept: () => {
          this.vlanService
            .deleteVlan(vlan.id)
            .subscribe({
              next: (response: any) => {
                this.editedVlanEvent.emit(null);
              },
              error: (err: HttpErrorResponse) => {
                this.errorHandler.handleError(err);
                let detail: string = "Unknown error";
                if (this.errorHandler.elementError) {
                  if (this.errorHandler.elementErrors.code == 1)
                    detail = "Can't delete VLAN. There is at least one IpPool attached to VLAN " + vlan.number;
                }
                this.messageService.add({
                  severity:'error',
                  summary:'deletion not possible',
                  detail: detail,
                  life: 6000
                });
              }
            })
        }
    });
}
}
