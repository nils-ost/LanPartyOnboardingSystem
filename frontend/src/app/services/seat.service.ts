import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Seat } from '../interfaces/seat';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SeatService {

  private seatUrl = environment.apiUrl + '/seat/';

  constructor(
    private http: HttpClient
  ) { }

  public getSeat(id: string): Observable<Seat> {
    return this.http.get<Seat>(this.seatUrl + id + '/', {withCredentials:true});
  }

  public getSeats(): Observable<Seat[]> {
    return this.http.get<Seat[]>(this.seatUrl, {withCredentials:true});
  }

  public createSeat(number: number, pw: string | null, table_id: string): Observable<any> {
    let seat = {
      'number': number,
      'pw': pw,
      'table_id': table_id
    }
    return this.http.post<any>(this.seatUrl, seat, {withCredentials:true});
  }

  public updateSeat(id: string, number: number, pw: string | null, table_id: string): Observable<any> {
    let seat = {
      'id': id,
      'number': number,
      'pw': pw,
      'table_id': table_id
    }
    return this.http.patch<any>(this.seatUrl + id + '/', seat, {withCredentials:true});
  }

  public updatePw(id: string, pw: string | null): Observable<any> {
    let seat = {
      'pw': pw
    }
    return this.http.patch<any>(this.seatUrl + id + '/', seat, {withCredentials:true});
  }

  public updateAbsoluteNumber(id: string, absnumber: number | null): Observable<any> {
    let seat = {
      'number_absolute': absnumber
    }
    return this.http.patch<any>(this.seatUrl + id + '/', seat, {withCredentials:true});
  }

  public deleteSeat(id: string): Observable<any> {
    return this.http.delete<any>(this.seatUrl + id + '/', {withCredentials:true});
  }
}
