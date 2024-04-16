from elements._elementBase import ElementBase, docDB


class Device(ElementBase):
    _attrdef = dict(
        mac=ElementBase.addAttr(unique=True, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        seat_id=ElementBase.addAttr(fk='Seat'),
        participant_id=ElementBase.addAttr(fk='Participant'),
        ip_pool_id=ElementBase.addAttr(fk='IpPool'),
        ip=ElementBase.addAttr(type=int, unique=True),
        port_id=ElementBase.addAttr(default=None, fk='Port'),
        onboarding_blocked=ElementBase.addAttr(type=bool, default=False),
        pw_strikes=ElementBase.addAttr(type=int, default=0)
    )

    @classmethod
    def get_by_mac(cls, mac):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'mac': mac})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_port(cls, port_id):
        result = list()
        for fromdb in docDB.search_many(cls.__name__, {'port_id': port_id}):
            r = cls()
            r._attr = fromdb
            result.append(r)
        return result

    @classmethod
    def get_by_seat(cls, seat_id):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'seat_id': seat_id})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_ip(cls, ip):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'ip': ip})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    def validate(self):
        errors = dict()
        if self['port_id'] is not None and docDB.get('Port', self['port_id']) is None:
            errors['port_id'] = {'code': 60, 'desc': f"There is no Port with id '{self['port_id']}'"}

        seat = docDB.get('Seat', self['seat_id'])
        if self['seat_id'] is not None:
            if seat is None:
                errors['seat_id'] = {'code': 60, 'desc': f"There is no Seat with id '{self['seat_id']}'"}
            else:
                seat_participant = docDB.search_one('Participant', {'seat_id': seat['_id']})
                self['participant_id'] = None
                if seat_participant is not None:
                    self['participant_id'] = seat_participant['_id']
                seat_table = docDB.get('Table', seat['table_id'])
                seat_ippool = docDB.get('IpPool', seat_table['seat_ip_pool_id'])
                self['ip_pool_id'] = seat_ippool['_id']
                self['ip'] = seat_ippool['range_start'] + seat['number'] - 1

        autoset_ip = False
        fromdb = None
        if self['_id'] is not None:
            fromdb = docDB.get('Device', self['_id'])
        participant = docDB.get('Participant', self['participant_id'])
        if self['participant_id'] is not None:
            if participant is None:
                errors['participant_id'] = {'code': 60, 'desc': f"There is no Participant with id '{self['participant_id']}'"}
            elif self['seat_id'] is None and self['ip_pool_id'] is None and participant['seat_id'] is not None:
                part_seat = docDB.get('Seat', participant['seat_id'])
                part_table = docDB.get('Table', part_seat['table_id'])
                self['ip_pool_id'] = part_table['add_ip_pool_id']
                if fromdb is None and self['ip'] is None:
                    autoset_ip = True
                elif fromdb is not None and not self['ip_pool_id'] == fromdb['ip_pool_id'] and self['ip'] == fromdb['ip']:
                    autoset_ip = True

        ippool = docDB.get('IpPool', self['ip_pool_id'])
        if self['ip_pool_id'] is not None:
            if ippool is None:
                errors['ip_pool_id'] = {'code': 60, 'desc': f"There is no IpPool with id '{self['ip_pool_id']}'"}
            elif participant is not None and not docDB.get('VLAN', ippool['vlan_id'])['purpose'] == 0:
                errors['ip_pool_id'] = {'code': 61, 'desc': 'Because Participant is set, Purpose of IpPools VLAN needs to be 0 (play)'}
            elif self['seat_id'] is None and docDB.search_one('Table', {'seat_ip_pool_id': self['ip_pool_id']}) is not None:
                errors['ip_pool_id'] = {'code': 62, 'desc': 'is used as seat_IpPool on Table and not allowed to be used directly by Device'}
            elif fromdb is None and self['ip'] is None:
                autoset_ip = True
            elif fromdb is not None and not self['ip_pool_id'] == fromdb['ip_pool_id'] and self['ip'] == fromdb['ip']:
                autoset_ip = True

        if autoset_ip:
            used_by_ippool = docDB.search_many('Device', {'ip_pool_id': self['ip_pool_id']})
            for number in range((ippool['range_end'] - ippool['range_start']) + 1):
                for used_device in used_by_ippool:
                    if used_device['ip'] == ippool['range_start'] + number:
                        break
                else:
                    self['ip'] = ippool['range_start'] + number
                    break

        if self['ip'] is not None:
            if ippool is None:
                errors['ip'] = {'code': 63, 'desc': 'can only be set if IpPool is set'}
            elif self['ip'] < ippool['range_start'] or self['ip'] > ippool['range_end']:
                errors['ip'] = {'code': 64, 'desc': 'not in range of IpPool'}
        return errors
