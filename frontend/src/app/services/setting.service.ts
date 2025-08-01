import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Setting } from '../interfaces/setting';
import { Observable } from 'rxjs';
import { ErrorHandlerService } from './error-handler.service';

@Injectable({
  providedIn: 'root'
})
export class SettingService {

  private settingUrl = environment.apiUrl + '/setting/';
  private cache: Map<string, any> = new Map<string, any>;

  constructor(
    private errorHandler: ErrorHandlerService,
    private http: HttpClient
  ) { }

  public getSetting(id: string): Observable<Setting> {
    return this.http.get<Setting>(this.settingUrl + id + '/', {withCredentials:true});
  }

  public getSettings(): Observable<Setting[]> {
    return this.http.get<Setting[]>(this.settingUrl, {withCredentials:true});
  }

  public updateSetting(id: string, value: any): Observable<Setting> {
    let setting = {'value': value};
    this.cache.delete(id);
    return this.http.patch<Setting>(this.settingUrl + id + '/', setting, {withCredentials:true});
  }
}
