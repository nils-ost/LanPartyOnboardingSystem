import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Setting } from '../interfaces/setting';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SettingService {

  private settingUrl = environment.apiUrl + '/setting/';

  constructor(
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
    return this.http.patch<Setting>(this.settingUrl + id + '/', setting, {withCredentials:true});
  }
}
