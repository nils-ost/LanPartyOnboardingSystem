import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { System } from '../interfaces/system';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SystemService {

  private systemUrl = environment.apiUrl + '/system/';

  constructor(
    private http: HttpClient
  ) { }

  public getSystem(): Observable<System> {
    return this.http.get<System>(this.systemUrl, {withCredentials:true});
  }

  public checkIntegrity(): Observable<any> {
    return this.http.get<any>(this.systemUrl + 'integrity/', {withCredentials:true});
  }

  public execCommitInterfaces(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_interfaces/', {}, {withCredentials:true});
  }

  public execRetreatInterfaces(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_interfaces/', {}, {withCredentials:true});
  }

  public execCommitDnsmasq(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_dnsmasq/', {}, {withCredentials:true});
  }

  public execRetreatDnsmasq(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_dnsmasq/', {}, {withCredentials:true});
  }

  public execCommitSwitches(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_switches/', {}, {withCredentials:true});
  }

  public execRetreatSwitches(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_switches/', {}, {withCredentials:true});
  }
}
