import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VlanCreaditComponent } from './vlan-creadit.component';

describe('VlanCreaditComponent', () => {
  let component: VlanCreaditComponent;
  let fixture: ComponentFixture<VlanCreaditComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ VlanCreaditComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VlanCreaditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
