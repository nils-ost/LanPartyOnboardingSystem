import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Switch, SwitchPurposeType } from 'src/app/interfaces/switch';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SwitchService } from 'src/app/services/switch.service';

@Component({
  selector: 'app-switches-list',
  templateUrl: './switches-list.component.html',
  styleUrls: ['./switches-list.component.scss']
})
export class SwitchesListComponent {
  switchPurposeType = SwitchPurposeType;
  @Input() switches!: Switch[];
  @Output() editedSwitchEvent = new EventEmitter<null>();
  editDialog: boolean = false;
  selectedSwitch!: Switch;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private errorHandler: ErrorHandlerService,
    private switchService: SwitchService
  ) {}

  editSwitch(sw: Switch) {
    this.selectedSwitch = sw;
    this.editDialog = true;
  }

  editedSwitch() {
    this.editDialog = false;
    this.editedSwitchEvent.emit(null);
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
