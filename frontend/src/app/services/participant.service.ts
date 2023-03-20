import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Participant } from '../interfaces/participant';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ParticipantService {

  private participantUrl = environment.apiUrl + '/participant/';

  constructor(
    private http: HttpClient
  ) { }

  public getParticipant(id: string): Observable<Participant> {
    return this.http.get<Participant>(this.participantUrl + id + '/', {withCredentials:true});
  }

  public getParticipants(): Observable<Participant[]> {
    return this.http.get<Participant[]>(this.participantUrl, {withCredentials:true});
  }

  public createParticipant(
          name: string,
          admin: boolean = false,
          login: string | null = null,
          pw: string | null = null,
          seat_id: string | null = null
        ): Observable<any> {
    let participant = {
      'admin': admin,
      'name': name,
      'login': login,
      'pw': pw,
      'seat_id': seat_id
    }
    return this.http.post<any>(this.participantUrl, participant, {withCredentials:true});
  }

  public updateParticipant(id: string, admin: boolean, name: string, login: string | null, pw: string | null, seat_id: string | null): Observable<any> {
    let participant = {
      'id': id,
      'admin': admin,
      'name': name,
      'login': login,
      'pw': pw,
      'seat_id': seat_id
    }
    return this.http.patch<any>(this.participantUrl + id + '/', participant, {withCredentials:true});
  }

  public deleteParticipant(id: string): Observable<any> {
    return this.http.delete<any>(this.participantUrl + id + '/', {withCredentials:true});
  }
}
