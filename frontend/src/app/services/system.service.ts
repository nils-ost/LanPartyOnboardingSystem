import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { System } from '../interfaces/system';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SystemService {

  private switchUrl = environment.apiUrl + '/system/';

  constructor(
    private http: HttpClient
  ) { }

  public getSystem(): Observable<System> {
    return this.http.get<System>(this.switchUrl, {withCredentials:true});
  }

  public execCommit(): Observable<any> {
    return this.http.post<any>(this.switchUrl + 'commit/', {}, {withCredentials:true});
  }

  public execRetreat(): Observable<any> {
    return this.http.post<any>(this.switchUrl + 'retreat/', {}, {withCredentials:true});
  }
}
