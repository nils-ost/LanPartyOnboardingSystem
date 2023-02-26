import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NetworkScreenComponent } from './network-screen.component';

describe('NetworkScreenComponent', () => {
  let component: NetworkScreenComponent;
  let fixture: ComponentFixture<NetworkScreenComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NetworkScreenComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NetworkScreenComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
