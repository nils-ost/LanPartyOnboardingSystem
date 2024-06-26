from elements._elementBase import ElementBase, docDB


class PortConfigCache(ElementBase):
    _attrdef = dict(
        port_id=ElementBase.addAttr(notnone=True, fk='Port'),
        scope=ElementBase.addAttr(type=int, notnone=True),
        skip=ElementBase.addAttr(type=bool, default=False, notnone=True),
        vlan_ids=ElementBase.addAttr(type=list, default=list(), notnone=True),
        default_vlan_id=ElementBase.addAttr(default=None, fk='VLAN'),
        enabled=ElementBase.addAttr(type=bool, default=True, notnone=True),
        mode=ElementBase.addAttr(default='optional', notnone=True),
        receive=ElementBase.addAttr(default='any', notnone=True),
        force=ElementBase.addAttr(type=bool, default=False, notnone=True)
    )

    @classmethod
    def get_by_port(cls, port_id, scope=0):
        from_db = docDB.search_one(cls.__name__, {'port_id': port_id, 'scope': scope})
        if from_db is not None:
            return cls(from_db)
        g = cls({'port_id': port_id, 'scope': scope})
        g._generate()
        return g

    @classmethod
    def delete_by_port(cls, port_id):
        docDB.delete_many(cls.__name__, {'port_id': port_id})

    def _generate(self):
        pass
