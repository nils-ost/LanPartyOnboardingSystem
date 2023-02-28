import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Vlan } from '../interfaces/vlan';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VlanService {

  private vlanUrl = environment.apiUrl + '/vlan/';

  constructor(
    private http: HttpClient
  ) { }

  public getVlan(id: string): Observable<Vlan> {
    return this.http.get<Vlan>(this.vlanUrl + id + '/', {withCredentials:true});
  }

  public getVlans(): Observable<Vlan[]> {
    return this.http.get<Vlan[]>(this.vlanUrl, {withCredentials:true});
  }

  public createVlan(number: number, purpose: number, desc: string): Observable<any> {
    let vlan = {'number': number, 'purpose': purpose, 'desc': desc};
    return this.http.post<Vlan>(this.vlanUrl, vlan, {withCredentials:true});
  }

  public updateVlan(id: string, number: number, purpose: number, desc: string): Observable<any> {
    let vlan = {'id': id, 'number': number, 'purpose': purpose, 'desc': desc};
    return this.http.patch<Vlan>(this.vlanUrl + id + '/', vlan, {withCredentials:true});
  }

  public deleteVlan(id: string): Observable<any> {
    return this.http.delete<any>(this.vlanUrl + id + '/', {withCredentials:true});
  }
}
