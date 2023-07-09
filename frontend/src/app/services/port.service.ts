import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Port } from '../interfaces/port';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PortService {

  private portUrl = environment.apiUrl + '/port/';

  constructor(
    private http: HttpClient
  ) { }

  public getPort(id: string): Observable<Port> {
    return this.http.get<Port>(this.portUrl + id + '/', {withCredentials:true});
  }

  public getPorts(): Observable<Port[]> {
    return this.http.get<Port[]>(this.portUrl, {withCredentials:true});
  }

  public updateDesc(id: string, desc: string): Observable<any> {
    let port = {
      'desc': desc
    }
    return this.http.patch<any>(this.portUrl + id + '/', port, {withCredentials:true});
  }

  public updateParticipants(id: string, participants: boolean): Observable<any> {
    let port = {
      'participants': participants
    }
    return this.http.patch<any>(this.portUrl + id + '/', port, {withCredentials:true});
  }

  public updateSwitchlinkPortId(id: string, switchlink_port_id: string | null): Observable<any> {
    let port = {
      'switchlink_port_id': switchlink_port_id
    }
    return this.http.patch<any>(this.portUrl + id + '/', port, {withCredentials:true});
  }
}
