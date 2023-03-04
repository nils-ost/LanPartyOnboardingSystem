import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { CardModule } from 'primeng/card';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { PanelModule } from 'primeng/panel';
import { ToastModule } from 'primeng/toast';

import { ConfirmationService } from 'primeng/api';
import { MessageService } from 'primeng/api';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { WelcomeComponent } from './components/welcome/welcome.component';
import { LoginComponent } from './components/login/login.component';
import { AutoFocusDirective } from './directives/auto-focus.directive';
import { VlansListComponent } from './components/vlans-list/vlans-list.component';
import { NetworkScreenComponent } from './components/network-screen/network-screen.component';
import { VlanCreaditComponent } from './components/vlan-creadit/vlan-creadit.component';
import { SwitchesListComponent } from './components/switches-list/switches-list.component';
import { SwitchCreaditComponent } from './components/switch-creadit/switch-creadit.component';
import { IpPoolsListComponent } from './components/ip-pools-list/ip-pools-list.component';
import { IpPoolCreaditComponent } from './components/ip-pool-creadit/ip-pool-creadit.component';

@NgModule({
  declarations: [
    AppComponent,
    WelcomeComponent,
    LoginComponent,
    AutoFocusDirective,
    VlansListComponent,
    NetworkScreenComponent,
    VlanCreaditComponent,
    SwitchesListComponent,
    SwitchCreaditComponent,
    IpPoolsListComponent,
    IpPoolCreaditComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    ButtonModule,
    InputTextModule,
    PasswordModule,
    CardModule,
    OverlayPanelModule,
    InputNumberModule,
    DropdownModule,
    TableModule,
    DialogModule,
    ConfirmDialogModule,
    PanelModule,
    ToastModule
  ],
  providers: [
    ConfirmationService,
    MessageService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
