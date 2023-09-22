import { Injectable } from '@angular/core';
import { SeatService } from './seat.service';
import { TableService } from './table.service';
import { Table } from '../interfaces/table';
import { Seat } from '../interfaces/seat';
import { delay } from 'rxjs/operators';
import { ErrorHandlerService } from './error-handler.service';
import { HttpErrorResponse } from '@angular/common/http';
import { IpPool } from '../interfaces/ip-pool';
import { IpPoolService } from './ip-pool.service';
import { Participant } from '../interfaces/participant';
import { ParticipantService } from './participant.service';
import { Port } from '../interfaces/port';
import { PortService } from './port.service';
import { Switch } from '../interfaces/switch';
import { SwitchService } from './switch.service';

@Injectable({
  providedIn: 'root'
})
export class UtilsService {
  tablesById: Map<string, Table | null> = new Map<string, Table | null>;
  seatsById: Map<string, Seat | null> = new Map<string, Seat | null>;
  ippoolsById: Map<string, IpPool | null> = new Map<string, IpPool | null>;
  participantById: Map<string, Participant | null> = new Map<string, Participant | null>;
  portById: Map<string, Port | null> = new Map<string, Port | null>;
  switchById: Map<string, Switch | null> = new Map<string, Switch | null>;

  constructor(
    private errorHandler: ErrorHandlerService,
    private seatService: SeatService,
    private ippoolService: IpPoolService,
    private tableService: TableService,
    private participantService: ParticipantService,
    private portService: PortService,
    private switchService: SwitchService
  ) { }

  public ip_int_to_str(ip: number | null): string {
    if (!ip) return '---';
    let result: string = "";
    let hex = ip.toString(16);
    if (hex.length < 8) hex = '0' + hex;
    result = result + parseInt(hex.slice(0, 2), 16).toString() + '.';
    result = result + parseInt(hex.slice(2, 4), 16).toString() + '.';
    result = result + parseInt(hex.slice(4, 6), 16).toString() + '.';
    result = result + parseInt(hex.slice(6, 8), 16).toString();
    return result;
  }

  public seatIdToReadable(id: string | null): string {
    if (!id) return '---';
    let seat: Seat = this.pullSeat(id);
    let table: Table = this.pullTable(seat.table_id);
    return table.number + '(' + table.desc + ')' + ': #' + seat.number
  }

  public ipPoolIdToReadable(id: string): string {
    if (!id) return '---';
    let pool: IpPool = this.pullIpPool(id);
    return pool.desc;
  }

  public participantIdToReadable(id: string): string {
    if (!id) return '---';
    let participant: Participant = this.pullParticipant(id);
    return participant.name + '(' + participant.login + ')';
  }

  public portIdToReadable(id: string): string {
    if (!id) return '---';
    let port: Port = this.pullPort(id);
    let swi: Switch = this.pullSwitch(port.switch_id);
    return swi.desc + ': #' + port.number;
  }

  private pullSeat(id: string) {
    let seat: Seat | undefined | null = this.seatsById.get(id);
    if (seat == undefined) {
      this.seatsById.set(id, null);
      this.seatService
        .getSeat(id)
        .subscribe({
          next: (seat: Seat) => {
            this.seatsById.set(id, seat);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (seat == null) {
      delay(50);
      seat = this.seatsById.get(id);
    }
    return seat;
  }

  private pullTable(id: string): Table {
    let table: Table | undefined | null = this.tablesById.get(id);
    if (table == undefined) {
      this.tablesById.set(id, null);
      this.tableService
        .getTable(id)
        .subscribe({
          next: (table: Table) => {
            this.tablesById.set(id, table);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (table == null) {
      delay(50);
      table = this.tablesById.get(id);
    }
    return table;
  }

  private pullIpPool(id: string): IpPool {
    let pool: IpPool | undefined | null = this.ippoolsById.get(id);
    if (pool == undefined) {
      this.ippoolsById.set(id, null);
      this.ippoolService
        .getIpPool(id)
        .subscribe({
          next: (pool: IpPool) => {
            this.ippoolsById.set(id, pool);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (pool == null) {
      delay(50);
      pool = this.ippoolsById.get(id);
    }
    return pool;
  }

  private pullParticipant(id: string): Participant {
    let p: Participant | undefined | null = this.participantById.get(id);
    if (p == undefined) {
      this.participantById.set(id, null);
      this.participantService
        .getParticipant(id)
        .subscribe({
          next: (p: Participant) => {
            this.participantById.set(id, p);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (p == null) {
      delay(50);
      p = this.participantById.get(id);
    }
    return p;
  }

  private pullPort(id: string): Port {
    let p: Port | undefined | null = this.portById.get(id);
    if (p == undefined) {
      this.portById.set(id, null);
      this.portService
        .getPort(id)
        .subscribe({
          next: (p: Port) => {
            this.portById.set(id, p);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (p == null) {
      delay(50);
      p = this.portById.get(id);
    }
    return p;
  }

  private pullSwitch(id: string): Switch {
    let s: Switch | undefined | null = this.switchById.get(id);
    if (s == undefined) {
      this.switchById.set(id, null);
      this.switchService
        .getSwitch(id)
        .subscribe({
          next: (s: Switch) => {
            this.switchById.set(id, s);
          },
          error: (err: HttpErrorResponse) => {
            this.errorHandler.handleError(err);
          }
        });
    }
    while (s == null) {
      delay(50);
      s = this.switchById.get(id);
    }
    return s;
  }
}
