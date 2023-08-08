import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class UtilsService {

  constructor() { }

  public ip_int_to_str(ip: number): string {
    let result: string = "";
    let hex = ip.toString(16);
    if (hex.length < 8) hex = '0' + hex;
    result = result + parseInt(hex.slice(0, 2), 16).toString() + '.';
    result = result + parseInt(hex.slice(2, 4), 16).toString() + '.';
    result = result + parseInt(hex.slice(4, 6), 16).toString() + '.';
    result = result + parseInt(hex.slice(6, 8), 16).toString();
    return result;
  }
}
