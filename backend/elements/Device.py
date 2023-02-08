from elements._elementBase import ElementBase, docDB


class Device(ElementBase):
    _attrdef = dict(
        mac=ElementBase.addAttr(unique=True, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        seat_id=ElementBase.addAttr(),
        participant_id=ElementBase.addAttr(),
        ip_pool_id=ElementBase.addAttr(),
        ip=ElementBase.addAttr(type=int, unique=True)
    )

    def validate(self):
        errors = dict()
        seat = docDB.get('Seat', self['seat_id'])
        if self['seat_id'] is not None:
            if seat is None:
                errors['seat_id'] = f"There is no Seat with id '{self['seat_id']}'"
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
                errors['participant_id'] = f"There is no Participant with id '{self['participant_id']}'"
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
                errors['ip_pool_id'] = f"There is no IpPool with id '{self['ip_pool_id']}'"
            elif participant is not None and not docDB.get('VLAN', ippool['vlan_id'])['purpose'] == 0:
                errors['ip_pool_id'] = 'Because Participant is set, Purpose of IpPools VLAN needs to be 0 (play)'
            elif self['seat_id'] is None and docDB.search_one('Table', {'seat_ip_pool_id': self['ip_pool_id']}) is not None:
                errors['ip_pool_id'] = 'is used as seat_IpPool on Table and not allowed to be used directly by Device'
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
                errors['ip'] = 'can only be set if IpPool is set'
            elif self['ip'] < ippool['range_start'] or self['ip'] > ippool['range_end']:
                errors['ip'] = 'not in range of IpPool'
        return errors
