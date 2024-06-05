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

  public execCommitDnsServers(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_dns_servers/', {}, {withCredentials:true});
  }

  public execRetreatDnsServers(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_dns_servers/', {}, {withCredentials:true});
  }

  public execCommitDhcpServers(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_dhcp_servers/', {}, {withCredentials:true});
  }

  public execRetreatDhcpServers(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_dhcp_servers/', {}, {withCredentials:true});
  }

  public execCommitSwitches(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_switches/', {}, {withCredentials:true});
  }

  public execRetreatSwitches(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat_switches/', {}, {withCredentials:true});
  }

  public execCommitHaproxy(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit_haproxy/', {}, {withCredentials:true});
  }
}
