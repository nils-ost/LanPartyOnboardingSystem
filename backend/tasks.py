from invoke import task


@task(name='coverage')
def coverage(c):
    c.run('coverage erase && coverage run --concurrency=multiprocessing -m unittest discover; coverage combine && coverage html && coverage report')


@task(name='create-admin')
def create_admin(c):
    from elements import Participant
    p = Participant.get_by_login('admin')
    if p is None:
        p = Participant()
    p['login'] = 'admin'
    p['pw'] = 'password'
    p['admin'] = True
    p.save()


@task(pre=[create_admin], name='create-testdata')
def create_testdata(c):
    from elements import VLAN, Switch, IpPool, Device, Port
    VLAN({'number': 1, 'purpose': 3, 'desc': 'default'}).save()
    v_mgmt = VLAN({'number': 2, 'purpose': 1, 'desc': 'mgmt'})
    v_mgmt.save()
    v_play = VLAN({'number': 3, 'purpose': 0, 'desc': 'play'})
    v_play.save()
    v_t1 = VLAN({'number': 4, 'purpose': 2, 'desc': 'table 1'})
    v_t1.save()
    v_t2 = VLAN({'number': 5, 'purpose': 2, 'desc': 'table 2'})
    v_t2.save()
    v_t3 = VLAN({'number': 6, 'purpose': 2, 'desc': 'table 3'})
    v_t3.save()
    s_core = Switch({'desc': 'C1', 'addr': '172.16.0.10', 'user': 'admin', 'pw': 'password1', 'purpose': 0})
    s_core.save()
    s_t1 = Switch({'desc': 'M1', 'addr': '172.16.0.11', 'user': 'admin', 'pw': 'password2', 'purpose': 2, 'onboarding_vlan_id': v_t1['_id']})
    s_t1.save()
    s_t2 = Switch({'desc': 'P2', 'addr': '172.16.0.12', 'user': 'admin', 'pw': 'password3', 'purpose': 1, 'onboarding_vlan_id': v_t2['_id']})
    s_t2.save()
    s_t3 = Switch({'desc': 'P3', 'addr': '172.16.0.13', 'user': 'admin', 'pw': 'password4', 'purpose': 1, 'onboarding_vlan_id': v_t3['_id']})
    s_t3.save()
    for s in [s_core, s_t1, s_t2, s_t3]:
        for i in range(12):
            p = Port({'number': i, 'switch_id': s['_id']})
            p.save()
    IpPool({'desc': 'switches', 'mask': 24, 'vlan_id': v_mgmt['_id'],
            'range_start': IpPool.octetts_to_int(172, 16, 0, 10), 'range_end': IpPool.octetts_to_int(172, 16, 0, 19)}).save()
    IpPool({'desc': 'onboarding table 1', 'mask': 24, 'vlan_id': v_t1['_id'],
            'range_start': IpPool.octetts_to_int(172, 16, 1, 1), 'range_end': IpPool.octetts_to_int(172, 16, 1, 30)}).save()
    IpPool({'desc': 'onboarding table 2', 'mask': 24, 'vlan_id': v_t2['_id'],
            'range_start': IpPool.octetts_to_int(172, 16, 1, 31), 'range_end': IpPool.octetts_to_int(172, 16, 1, 60)}).save()
    IpPool({'desc': 'onboarding table 3', 'mask': 24, 'vlan_id': v_t3['_id'],
            'range_start': IpPool.octetts_to_int(172, 16, 1, 61), 'range_end': IpPool.octetts_to_int(172, 16, 1, 90)}).save()
    IpPool({'desc': 'seats table 1', 'mask': 24, 'vlan_id': v_play['_id'],
            'range_start': IpPool.octetts_to_int(192, 168, 0, 110), 'range_end': IpPool.octetts_to_int(192, 168, 0, 119)}).save()
    IpPool({'desc': 'seats table 2', 'mask': 24, 'vlan_id': v_play['_id'],
            'range_start': IpPool.octetts_to_int(192, 168, 0, 120), 'range_end': IpPool.octetts_to_int(192, 168, 0, 129)}).save()
    IpPool({'desc': 'seats table 3', 'mask': 24, 'vlan_id': v_play['_id'],
            'range_start': IpPool.octetts_to_int(192, 168, 0, 130), 'range_end': IpPool.octetts_to_int(192, 168, 0, 139)}).save()
    IpPool({'desc': 'additional play', 'mask': 24, 'vlan_id': v_play['_id'],
            'range_start': IpPool.octetts_to_int(192, 168, 0, 160), 'range_end': IpPool.octetts_to_int(192, 168, 0, 200)}).save()
    if Device.get_by_mac('localhost') is None:
        Device({'mac': 'localhost'}).save()
    counter = 1
    for s in [s_core, s_t1, s_t2, s_t3]:
        for i in range(3, 5):
            d = Device({'mac': f'testdevice{counter}'})
            counter += 1
            d.port(Port.get_by_number(switch_id=s['_id'], number=i))
            d.save()
    for i in range(3):  # to have one port with multiple devices
        d = Device({'mac': f'testdevice{counter}'})
        counter += 1
        d.port(Port.get_by_number(switch_id=s_core['_id'], number=6))
        d.save()


@task(pre=[create_admin], name='create-nlpt')
def create_nlpt_testdata(c):
    from elements import VLAN, Switch, Device
    VLAN({'number': 1, 'purpose': 3, 'desc': 'default'}).save()
    v_mgmt = VLAN({'number': 2, 'purpose': 1, 'desc': 'mgmt'})
    v_mgmt.save()
    v_play = VLAN({'number': 3, 'purpose': 0, 'desc': 'play'})
    v_play.save()
    v_t1 = VLAN({'number': 4, 'purpose': 2, 'desc': 'table 1'})
    v_t1.save()
    v_t2 = VLAN({'number': 5, 'purpose': 2, 'desc': 'table 2'})
    v_t2.save()
    v_t3 = VLAN({'number': 6, 'purpose': 2, 'desc': 'table 3'})
    v_t3.save()
    v_t4 = VLAN({'number': 7, 'purpose': 2, 'desc': 'table 4'})
    v_t4.save()
    s_c1 = Switch({'addr': 'c1.nlpt.sani.network', 'desc': 'c1', 'user': 'admin', 'pw': 'password', 'purpose': 0})
    s_c1.save()
    s_c2 = Switch({'addr': 'c2.nlpt.sani.network', 'desc': 'c2', 'user': 'admin', 'pw': 'password', 'purpose': 0})
    s_c2.save()
    s_t1 = Switch({'addr': 'p1.nlpt.sani.network', 'desc': 'p1', 'user': 'admin', 'pw': 'password', 'purpose': 1, 'onboarding_vlan_id': v_t1['_id']})
    s_t1.save()
    s_t2 = Switch({'addr': 'p2.nlpt.sani.network', 'desc': 'p2', 'user': 'admin', 'pw': 'password', 'purpose': 1, 'onboarding_vlan_id': v_t2['_id']})
    s_t2.save()
    s_t3 = Switch({'addr': 'p3.nlpt.sani.network', 'desc': 'p3', 'user': 'admin', 'pw': 'password', 'purpose': 1, 'onboarding_vlan_id': v_t3['_id']})
    s_t3.save()
    s_t4 = Switch({'addr': 'p4.nlpt.sani.network', 'desc': 'p4', 'user': 'admin', 'pw': 'password', 'purpose': 1, 'onboarding_vlan_id': v_t4['_id']})
    s_t4.save()
    if Device.get_by_mac('localhost') is None:
        Device({'mac': 'localhost'}).save()


@task(name='reset-switch', aliases=['rs', ])
def reset_switch(c):
    from MTSwitch import MikroTikSwitch
    addr = input('Addr: ').strip()
    user = input('User (admin): ').strip()
    if user == '':
        user = 'admin'
    pw = input('PW: ').strip()
    s = MikroTikSwitch(addr, user, pw)
    if s.connected:
        vlan_ids = list()
        for vlan in s.vlans:
            vlan_ids.append(vlan.id)
        if 1 not in vlan_ids:
            s.vlanAdd(1)
        else:
            vlan_ids.remove(1)
        for port in s.ports:
            s.portEdit(port, enabled=True, vmode='optional', vreceive='any', vdefault=1, vforce=False)
            for p in range(len(s.ports)):
                if p == port.idx:
                    continue
                s.portEdit(port, fwdTo=p)
            s.vlanEdit(1, memberAdd=port)
        for v in vlan_ids:
            s.vlanRemove(v)
        s.commitAll()
    else:
        print(f'No connection to: {addr}')
