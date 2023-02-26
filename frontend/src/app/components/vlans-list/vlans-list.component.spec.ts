import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VlansListComponent } from './vlans-list.component';

describe('VlansListComponent', () => {
  let component: VlansListComponent;
  let fixture: ComponentFixture<VlansListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ VlansListComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VlansListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
