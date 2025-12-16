import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class UtilsService {

  constructor(
  ) { }

  public ip_int_to_octetts(addr: number): number[] {
    let list: number[] = [];
    let hex = addr.toString(16);
    if (hex.length < 8) hex = '0' + hex;
    list.push(parseInt(hex.slice(0, 2), 16));
    list.push(parseInt(hex.slice(2, 4), 16));
    list.push(parseInt(hex.slice(4, 6), 16));
    list.push(parseInt(hex.slice(6, 8), 16));
    return list;
  }

  public ip_octetts_to_int(oct: number[]): number {
    let hex = '';
    for (let i = 0; i < oct.length; i++) {
      if (oct[i] < 0) oct[i] = 0;
      if (oct[i] > 255) oct[i] = 255;
      let ohex = oct[i].toString(16);
      if (ohex.length < 2) ohex = '0' + ohex;
      hex = hex + ohex;
    }
    return parseInt(hex, 16);
  }

  public ip_int_to_str(ip: number | null): string {
    if (!ip) return '---';
    let list: string[] = [];
    for (let element of this.ip_int_to_octetts(ip)) list.push(element.toString());
    return list.join('.');
  }

  public ip_apply_mask(addr: number, prefix_len: number): number {
    let mask: number = (((2 ** prefix_len) - 1) << (32 - prefix_len)) >>>0;
    return (addr & mask) >>>0;
  }
}
