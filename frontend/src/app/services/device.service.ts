import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Device } from '../interfaces/device';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class DeviceService {

  private deviceUrl = environment.apiUrl + '/device/';

  constructor(
    private http: HttpClient
  ) { }

  public getDevice(id: string): Observable<Device> {
    return this.http.get<Device>(this.deviceUrl + id + '/', {withCredentials:true});
  }

  public getDevices(): Observable<Device[]> {
    return this.http.get<Device[]>(this.deviceUrl, {withCredentials:true});
  }

  public createDevice(mac: string, desc: string, seat_id: string | null, participant_id: string | null, ip_pool_id: string | null, ip: number | null): Observable<any> {
    let device = {
      'mac': mac,
      'desc': desc,
      'seat_id': seat_id,
      'participant_id': participant_id,
      'ip_pool_id': ip_pool_id,
      'ip': ip
    }
    return this.http.post<any>(this.deviceUrl, device, {withCredentials:true});
  }

  public updateDevice(id: string, mac: string, desc: string, seat_id: string | null, participant_id: string | null, ip_pool_id: string | null, ip: number | null): Observable<any> {
    let device = {
      'id': id,
      'mac': mac,
      'desc': desc,
      'seat_id': seat_id,
      'participant_id': participant_id,
      'ip_pool_id': ip_pool_id,
      'ip': ip
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', device, {withCredentials:true});
  }

  public updateDesc(id: string, desc: string): Observable<any> {
    let device = {
      'id': id,
      'desc': desc
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', device, {withCredentials:true});
  }

  public updateBlocked(id: string, blocked: boolean, strikes: number = 0): Observable<any> {
    if (!blocked) strikes = 0;
    let device = {
      'id': id,
      'onboarding_blocked': blocked,
      'pw_strikes': strikes
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', device, {withCredentials:true});
  }

  public updateSeatId(id: string, seat_id: string | null): Observable<any> {
    let device = {
      'id': id,
      'seat_id': seat_id
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', device, {withCredentials:true});
  }

  public removeSeat(id: string): Observable<any> {
    let device = {
      'id': id,
      'seat_id': null,
      'participant_id': null,
      'ip_pool_id': null,
      'ip': null
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', device, {withCredentials:true});
  }

  public deleteDevice(id: string): Observable<any> {
    return this.http.delete<any>(this.deviceUrl + id + '/', {withCredentials:true});
  }

  public updateVlanConfig(id: string, commit_config: any, retreat_config: any): Observable<any> {
    let port = {
      'commit_config': commit_config,
      'retreat_config': retreat_config
    }
    return this.http.patch<any>(this.deviceUrl + id + '/', port, {withCredentials:true});
  }
}
