import { Component, Input } from '@angular/core';
import { Participant } from 'src/app/interfaces/participant';

@Component({
  selector: 'app-participants-list',
  templateUrl: './participants-list.component.html',
  styleUrls: ['./participants-list.component.scss']
})
export class ParticipantsListComponent {
  @Input() participants!: Participant[];

}
