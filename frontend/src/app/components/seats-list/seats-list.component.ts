import { Component, Input, OnChanges } from '@angular/core';
import { Seat } from 'src/app/interfaces/seat';
import { Table } from 'src/app/interfaces/table';

@Component({
  selector: 'app-seats-list',
  templateUrl: './seats-list.component.html',
  styleUrls: ['./seats-list.component.scss']
})
export class SeatsListComponent implements OnChanges {
  @Input() tables!: Table[];
  @Input() seats!: Seat[];
  @Input() selectedTable?: Table;

  displaySeats: any[] = [];
  tablesNumbers: Map<string, number> = new Map<string, number>;

  ngOnChanges(): void {
    for (let i = 0; i < this.tables.length; i++) {
      let table: Table = this.tables[i];
      this.tablesNumbers.set(table.id, table.number);
    }

    let newList: any[] = [];
    if (this.selectedTable) {
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        if (this.selectedTable.id == seat.table_id) {
          let element = {
            table: this.tablesNumbers.get(seat.table_id),
            seatNumber: seat.number,
            seat: seat
          }
          newList.push(element);
        }
      }
    }
    else {
      for (let i = 0; i < this.seats.length; i++) {
        let seat: Seat = this.seats[i];
        let element = {
          table: this.tablesNumbers.get(seat.table_id),
          seatNumber: seat.number,
          seat: seat
        }
        newList.push(element);
      }
    }
    this.displaySeats = newList;
  }
}
