import { Component } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Router } from "@angular/router"

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent {
  dockItems: MenuItem[] = [];

  constructor(
    private router: Router
  ) { }

  ngOnInit() {
    this.dockItems = [
      {
        label: 'Home',
        tooltipOptions: {
          tooltipLabel: 'Home',
          tooltipPosition: 'top',
          positionTop: 0,
          positionLeft: 15,
          showDelay: 100
        },
        icon: 'pi-home',
        command: () => {
          this.router.navigate(['/welcome']);
        }
      },
      {
        label: 'Network',
        tooltipOptions: {
          tooltipLabel: 'Network',
          tooltipPosition: 'top',
          positionTop: 0,
          positionLeft: 15,
          showDelay: 100
        },
        icon: 'pi-desktop',
        command: () => {
          this.router.navigate(['/network']);
        }
      },
      {
        label: 'Tables',
        tooltipOptions: {
          tooltipLabel: 'Tables',
          tooltipPosition: 'top',
          positionTop: 0,
          positionLeft: 15,
          showDelay: 100
        },
        icon: 'pi-th-large',
        command: () => {
          this.router.navigate(['/tables']);
        }
      },
      {
        label: 'Participants',
        tooltipOptions: {
          tooltipLabel: 'Participants',
          tooltipPosition: 'top',
          positionTop: 0,
          positionLeft: 15,
          showDelay: 100
        },
        icon: 'pi-users',
        command: () => {
          this.router.navigate(['/participants']);
        }
      },
      {
        label: 'Logout',
        tooltipOptions: {
          tooltipLabel: 'Logout',
          tooltipPosition: 'top',
          positionTop: 0,
          positionLeft: 15,
          showDelay: 100
        },
        icon: 'pi-sign-out',
        command: () => {
          this.router.navigate(['/logout']);
        }
      }
    ];
  }

}
