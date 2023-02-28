import { Component, OnInit, ViewChild } from '@angular/core';
import { ErrorHandlerService } from '../../services/error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { Vlan } from '../../interfaces/vlan';
import { VlanService } from '../../services/vlan.service';
import { SwitchService } from 'src/app/services/switch.service';
import { Switch } from 'src/app/interfaces/switch';

@Component({
  selector: 'app-network-screen',
  templateUrl: './network-screen.component.html',
  styleUrls: ['./network-screen.component.scss']
})
export class NetworkScreenComponent implements OnInit {
  @ViewChild('createvlan') createVlanDialog: any;
  vlans: Vlan[] = [];
  switches: Switch[] = [];

  constructor(
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService,
    private switchService: SwitchService
  ) { }

  ngOnInit(): void {
    this.refreshVlans();
    this.refreshSwitches();
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

  creaditVlan() {
    this.createVlanDialog.hide();
    this.refreshVlans();
  }

  creaditSwitch() {}

}
