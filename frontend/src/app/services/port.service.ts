import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Port, PortConfigCache } from '../interfaces/port';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PortService {

  private portUrl = environment.apiUrl + '/port/';
  private pccUrl = environment.apiUrl + '/portconfigcache/';

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

  public updateVlanConfig(id: string, commit_config: any, retreat_config: any, commit_disabled: boolean = false, retreat_disabled: boolean = false): Observable<any> {
    let port = {
      'commit_disabled': commit_disabled,
      'commit_config': commit_config,
      'retreat_disabled': retreat_disabled,
      'retreat_config': retreat_config
    }
    return this.http.patch<any>(this.portUrl + id + '/', port, {withCredentials:true});
  }

  public updateSwitchlinkPortId(id: string, switchlink_port_id: string | null): Observable<any> {
    let port = {
      'switchlink_port_id': switchlink_port_id
    }
    return this.http.patch<any>(this.portUrl + id + '/', port, {withCredentials:true});
  }

  public getCaches(): Observable<PortConfigCache[]> {
    return this.http.get<PortConfigCache[]>(this.pccUrl, {withCredentials:true})
  }

  public deleteAllCaches(): Observable<any> {
    return this.http.delete<any>(this.pccUrl, {withCredentials:true})
  }
}
