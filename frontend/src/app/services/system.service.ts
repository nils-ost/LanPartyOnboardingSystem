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

  public execCommit(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'commit/', {}, {withCredentials:true});
  }

  public execRetreat(): Observable<any> {
    return this.http.post<any>(this.systemUrl + 'retreat/', {}, {withCredentials:true});
  }
}
