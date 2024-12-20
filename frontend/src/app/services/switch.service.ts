import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Switch } from '../interfaces/switch';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SwitchService {

  private switchUrl = environment.apiUrl + '/switch/';

  constructor(
    private http: HttpClient
  ) { }

  public getSwitch(id: string): Observable<Switch> {
    return this.http.get<Switch>(this.switchUrl + id + '/', {withCredentials:true});
  }

  public getSwitches(): Observable<Switch[]> {
    return this.http.get<Switch[]>(this.switchUrl, {withCredentials:true});
  }

  public createSwitch(desc: string, addr: string, user: string, pw: string, purpose: number, onboarding_vlan_id: string | null): Observable<any> {
    let sw = {'desc': desc, 'addr': addr, 'user': user, 'pw': pw, 'purpose': purpose, 'onboarding_vlan_id': onboarding_vlan_id};
    return this.http.post<any>(this.switchUrl, sw, {withCredentials:true});
  }

  public updateSwitch(id: string, desc: string, addr: string, user: string, pw: string, purpose: number, onboarding_vlan_id: string | null): Observable<any> {
    let sw = {'id': id, 'desc': desc, 'addr': addr, 'user': user, 'pw': pw, 'purpose': purpose, 'onboarding_vlan_id': onboarding_vlan_id};
    return this.http.patch<any>(this.switchUrl + id + '/', sw, {withCredentials:true});
  }

  public dummySave(id: string): Observable<any> {
    let sw = {'id': id};
    return this.http.patch<any>(this.switchUrl + id + '/', sw, {withCredentials:true});
  }

  public updatePortNumberingOffset(id: string, pno: number): Observable<any> {
    let sw = {'id': id, 'port_numbering_offset': pno};
    return this.http.patch<any>(this.switchUrl + id + '/', sw, {withCredentials:true});
  }

  public deleteSwitch(id: string): Observable<any> {
    return this.http.delete<any>(this.switchUrl + id + '/', {withCredentials:true});
  }

  public execCommit(id: string): Observable<any> {
    return this.http.post<any>(this.switchUrl + 'commit/' + id + '/', {}, {withCredentials:true});
  }

  public execRetreat(id: string): Observable<any> {
    return this.http.post<any>(this.switchUrl + 'retreat/' + id + '/', {}, {withCredentials:true});
  }
}
