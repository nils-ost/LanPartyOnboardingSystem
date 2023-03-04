import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { IpPool } from '../interfaces/ip-pool';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IpPoolService {

  private ippoolUrl = environment.apiUrl + '/ippool/';

  constructor(
    private http: HttpClient
  ) { }

  public getIpPool(id: string): Observable<IpPool> {
    return this.http.get<IpPool>(this.ippoolUrl + '/', {withCredentials:true});
  }

  public getIpPools(): Observable<IpPool[]> {
    return this.http.get<IpPool[]>(this.ippoolUrl, {withCredentials:true});
  }

  public createIpPool(desc: string, mask: number, range_start: number, range_end: number, vlan_id: string): Observable<any> {
    let ippool = {'desc': desc, 'mask': mask, 'range_start': range_start, 'range_end': range_end, 'vlan_id': vlan_id};
    return this.http.post<any>(this.ippoolUrl, ippool, {withCredentials:true});
  }

  public updateIpPool(id: string, desc: string, mask: number, range_start: number, range_end: number, vlan_id: string): Observable<any> {
    let ippool = {'id': id, 'desc': desc, 'mask': mask, 'range_start': range_start, 'range_end': range_end, 'vlan_id': vlan_id};
    return this.http.patch<any>(this.ippoolUrl + id + '/', ippool, {withCredentials:true});
  }

  public deleteIpPool(id: string): Observable<any> {
    return this.http.delete<any>(this.ippoolUrl + id + '/', {withCredentials:true});
  }
}
