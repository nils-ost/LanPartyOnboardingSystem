import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { UtilsService } from 'src/app/services/utils.service';

@Component({
  selector: 'setting-ip-field',
  templateUrl: './setting-ip-field.component.html',
  styleUrls: ['./setting-ip-field.component.scss']
})
export class SettingIpFieldComponent implements OnInit {
  @Input() ip: number | null | undefined;
  @Output() ipChange = new EventEmitter<number>();
  @Input() inputId: string = 'ipfield';
  @Input() label: string = "";

  oct1: number | undefined;
  oct2: number | undefined;
  oct3: number | undefined;
  oct4: number | undefined;

  constructor(
    private utils: UtilsService
  ) {}

  ngOnInit(): void {
    if (this.ip) {
      let octetts: number[] = this.utils.ip_int_to_octetts(this.ip);
      this.oct1 = octetts[0];
      this.oct2 = octetts[1];
      this.oct3 = octetts[2];
      this.oct4 = octetts[3];
    }
  }

  update_ip() {
    console.log('update' + this.oct1 + ' ' + this.oct2 + ' ' + this.oct3 + ' ' + this.oct4);
    if (this.oct1 != undefined && this.oct2 != undefined && this.oct3 != undefined && this.oct4 != undefined) {
      this.ip = this.utils.ip_octetts_to_int([this.oct1, this.oct2, this.oct3, this.oct4]);
      this.ipChange.emit(this.ip);
      console.log(this.ip);
    }
  }
}
