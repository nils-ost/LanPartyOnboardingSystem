import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { WelcomeComponent } from './components/welcome/welcome.component';
import { LoginComponent } from './components/login/login.component';
import { LogoutComponent } from './components/logout/logout.component';
import { NetworkScreenComponent } from './components/network-screen/network-screen.component';
import { TablesScreenComponent } from './components/tables-screen/tables-screen.component';
import { ParticipantsScreenComponent } from './components/participants-screen/participants-screen.component';
import { OnboardingComponent } from './components/onboarding/onboarding.component';
import { DevicesScreenComponent } from './components/devices-screen/devices-screen.component';
import { SettingsScreenComponent } from './components/settings-screen/settings-screen.component';

const routes: Routes = [
  { path: 'welcome', component: WelcomeComponent },
  { path: 'network', component: NetworkScreenComponent },
  { path: 'tables', component: TablesScreenComponent },
  { path: 'participants', component: ParticipantsScreenComponent},
  { path: 'devices', component: DevicesScreenComponent},
  { path: 'devices/:port_id', component: DevicesScreenComponent},
  { path: 'login', component: LoginComponent },
  { path: 'logout', component: LogoutComponent },
  { path: 'onboarding', component: OnboardingComponent },
  { path: 'settings', component: SettingsScreenComponent },
  { path: '**', component: WelcomeComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
