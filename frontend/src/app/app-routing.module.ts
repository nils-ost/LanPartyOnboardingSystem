import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { WelcomeComponent } from './components/welcome/welcome.component';
import { LoginComponent } from './components/login/login.component';
import { NetworkScreenComponent } from './components/network-screen/network-screen.component';

const routes: Routes = [
  { path: 'welcome', component: WelcomeComponent },
  { path: 'network', component: NetworkScreenComponent },
  { path: 'login', component: LoginComponent },
  { path: '**', component: WelcomeComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
