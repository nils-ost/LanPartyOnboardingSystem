import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { Port } from 'src/app/interfaces/port';
import { Switch } from 'src/app/interfaces/switch';
import { Vlan } from 'src/app/interfaces/vlan';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { PortService } from 'src/app/services/port.service';

@Component({
  selector: 'app-ports-list',
  templateUrl: './ports-list.component.html',
  styleUrls: ['./ports-list.component.scss']
})
export class PortsListComponent implements OnChanges, OnInit {
  @Input() ports: Port[] = [];
  @Input() vlans: Vlan[] = [];
  @Input() selectedSwitch?: Switch;
  @Output() editedPortEvent = new EventEmitter<null>();

  @ViewChild('editdesc') editDescDialog: any;

  vlansNames: Map<string, string> = new Map<string, string>;
  displayPorts: Port[] =[];
  selectedPort: Port | undefined;
  newDesc: string = "";

  constructor(
    private errorHandler: ErrorHandlerService,
    private portService: PortService
  ) {}

  ngOnInit(): void {
    this.refreshVlanNames();
    this.refreshDisplay();
  }

  ngOnChanges(): void {
    this.refreshVlanNames();
    this.refreshDisplay();
  }

  refreshDisplay() {
    if (this.selectedSwitch) {
      let newList: Port[] = [];
      for (let i = 0; i < this.ports.length; i++) {
        let port: Port = this.ports[i];
        if (port.switch_id === this.selectedSwitch.id) newList.push(port);
      }
      this.displayPorts = newList;
    }
    else this.displayPorts = this.ports;
  }

  refreshVlanNames() {
    for (let i: number = 0; i < this.vlans.length; i++) {
      let vlan = this.vlans[i];
      this.vlansNames.set(vlan.id, vlan.number + ': ' + vlan.desc);
    }
  }

  editDescStart(port: Port, event: any) {
    this.selectedPort = port;
    this.newDesc = port.desc;
    this.editDescDialog.show(event);
  }

  editDesc() {
    if (this.selectedPort) {
      this.portService
        .updateDesc(this.selectedPort.id, this.newDesc)
        .subscribe({
          next: (response: any) => {
            this.editedPortEvent.emit(null);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        })
    }
    this.selectedPort = undefined;
    this.editDescDialog.hide();
  }

  editParticipants(port: Port, newValue: boolean) {
    this.portService
      .updateParticipants(port.id, newValue)
      .subscribe({
        next: (response: any) => {
          this.editedPortEvent.emit(null);
        },
        error: (err: HttpErrorResponse) => {
          this.errorHandler.handleError(err);
        }
      })
  }

}
