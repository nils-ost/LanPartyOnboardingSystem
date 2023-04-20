import { Component, OnInit, ViewChild } from '@angular/core';
import { ErrorHandlerService } from '../../services/error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { Vlan } from '../../interfaces/vlan';
import { VlanService } from '../../services/vlan.service';
import { Switch } from 'src/app/interfaces/switch';
import { SwitchService } from 'src/app/services/switch.service';
import { IpPool } from 'src/app/interfaces/ip-pool';
import { IpPoolService } from 'src/app/services/ip-pool.service';
import { Port } from 'src/app/interfaces/port';
import { PortService } from 'src/app/services/port.service';

@Component({
  selector: 'app-network-screen',
  templateUrl: './network-screen.component.html',
  styleUrls: ['./network-screen.component.scss']
})
export class NetworkScreenComponent implements OnInit {
  @ViewChild('createvlan') createVlanDialog: any;
  @ViewChild('createswitch') createSwitchDialog: any;
  @ViewChild('createippool') createIpPoolDialog: any;
  vlans: Vlan[] = [];
  switches: Switch[] = [];
  ippools: IpPool[] = [];
  ports: Port[] = [];

  constructor(
    private errorHandler: ErrorHandlerService,
    private vlanService: VlanService,
    private switchService: SwitchService,
    private ippoolService: IpPoolService,
    private portService: PortService
  ) { }

  ngOnInit(): void {
    this.refreshVlans();
    this.refreshSwitches();
    this.refreshIpPools();
    this.refreshPorts();
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

}
