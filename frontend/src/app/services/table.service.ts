import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Table } from '../interfaces/table';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TableService {

  private tableUrl = environment.apiUrl + '/table/';

  constructor(
    private http: HttpClient
  ) { }

  public getTable(id: string): Observable<Table> {
    return this.http.get<Table>(this.tableUrl + id + '/', {withCredentials:true});
  }

  public getTables(): Observable<Table[]> {
    return this.http.get<Table[]>(this.tableUrl, {withCredentials:true});
  }

  public createTable(number: number, desc: string, switch_id: string, seat_ip_pool_id: string, add_ip_pool_id: string):  Observable<any> {
    let table = {
      'number': number,
      'desc': desc,
      'switch_id': switch_id,
      'seat_ip_pool_id': seat_ip_pool_id,
      'add_ip_pool_id': add_ip_pool_id
    }
    return this.http.post<any>(this.tableUrl, table, {withCredentials:true});
  }

  public updateTable(id: string, number: number, desc: string, switch_id: string, seat_ip_pool_id: string, add_ip_pool_id: string): Observable<any> {
    let table = {
      'id': id,
      'number': number,
      'desc': desc,
      'switch_id': switch_id,
      'seat_ip_pool_id': seat_ip_pool_id,
      'add_ip_pool_id': add_ip_pool_id
    }
    return this.http.patch<any>(this.tableUrl + id + '/', table, {withCredentials:true});
  }

  public deleteTable(id: string): Observable<any> {
    return this.http.delete<any>(this.tableUrl + id + '/', {withCredentials:true});
  }
}
