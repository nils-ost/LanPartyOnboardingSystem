import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Router } from "@angular/router"

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit, OnChanges{
  @Input() missingLogin: boolean = false;
  menuItems: MenuItem[] = [];

  constructor(
    private router: Router
  ) { }

  ngOnChanges(changes: SimpleChanges): void {
    this.selectMenu();
  }

  ngOnInit(): void {
    this.selectMenu();
  }

  selectMenu() {
    if (this.missingLogin)
      this.menuItems = [
        {
          tooltipOptions: {
            tooltipLabel: 'Login',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-sign-in',
          command: () => {
            this.router.navigate(['/login']);
          }
        }
      ]
    else
      this.menuItems = [
        {
          tooltipOptions: {
            tooltipLabel: 'Home',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-home',
          command: () => {
            this.router.navigate(['/welcome']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Network',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-sitemap',
          command: () => {
            this.router.navigate(['/network']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Tables',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-th-large',
          command: () => {
            this.router.navigate(['/tables']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Participants',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-users',
          command: () => {
            this.router.navigate(['/participants']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Devices',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-desktop',
          command: () => {
            this.router.navigate(['/devices']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Settings',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-cog',
          command: () => {
            this.router.navigate(['/settings']);
          }
        },
        {
          tooltipOptions: {
            tooltipLabel: 'Logout',
            tooltipPosition: 'top',
            showDelay: 100
          },
          icon: 'pi pi-sign-out',
          command: () => {
            this.router.navigate(['/logout']);
          }
        }
      ];
  }

}
