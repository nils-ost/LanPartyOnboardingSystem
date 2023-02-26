import { Component, OnInit, ViewChild } from '@angular/core';
import { ErrorHandlerService } from '../../services/error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { Vlan } from '../../interfaces/vlan';
import { VlanService } from '../../services/vlan.service';

@Component({
  selector: 'app-network-screen',
  templateUrl: './network-screen.component.html',
  styleUrls: ['./network-screen.component.scss']
})
export class NetworkScreenComponent implements OnInit {
  @ViewChild('createvlan') createVlanDialog: any;
  vlans: Vlan[] = [];

  constructor(
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService
  ) { }

  ngOnInit(): void {
    this.refreshVlans();
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

  creaditVlan() {
    this.createVlanDialog.hide();
    this.refreshVlans();
  }

}
