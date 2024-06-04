import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class OnlineCheckService {

  private checkUrl = 'https://ipapi.co/json/';

  constructor(
    private http: HttpClient
  ) { }

  public execute(): Observable<any> {
    return this.http.get<any>(this.checkUrl);
  }
}
