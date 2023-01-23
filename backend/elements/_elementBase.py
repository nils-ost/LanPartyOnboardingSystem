from helpers.docdb import docDB


class ElementBase(object):
    _attrdef = dict()

    def __init__(self, attr=None):
        self._cache = dict()
        self._attr = dict()
        if '_id' not in self.__class__._attrdef.keys():
            self.__class__._attrdef = {**{'_id': self.__class__.addAttr(type=str, default=None, unique=True)}, **self.__class__._attrdef}  # add _id on front
        self.__init_attr()
        if attr is not None:
            for k, v in attr.items():
                self[k] = v

    def __init_attr(self):
        for name in self.__class__._attrdef.keys():
            self._attr[name] = self.__class__._attrdef[name]['default']

    def __getitem__(self, key):
        return self._attr.get(key, None)

    def __setitem__(self, key, value):
        if key in self._attr:
            self._attr[key] = value

    def __str__(self):
        return str(self._attr)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self['_id']}>"

    def addAttr(type=str, default=None, unique=False, notnone=False):
        return {'type': type, 'default': default, 'unique': unique, 'notnone': notnone}

    @classmethod
    def get(cls, id):
        result = cls()
        fromdb = docDB.get(cls.__name__, id)
        if fromdb is not None:
            result._attr = fromdb
        return result

    @classmethod
    def all(cls):
        result = list()
        for element in docDB.search_many(cls.__name__, {}):
            result.append(cls(element))
        return result

    def validate_base(self):
        errors = dict()
        for attr, opt in self.__class__._attrdef.items():
            if attr == '_id':
                continue
            if opt['notnone']:
                if self[attr] is None:
                    errors[attr] = 'marked as not to be None'
                    continue
            if opt['unique']:
                found = docDB.search_one(self.__class__.__name__, {attr: self[attr]})
                if found is not None and not found['_id'] == self['_id']:
                    errors[attr] = f'marked as unique, but element with value "{self[attr]}" allready present'
                    continue
            if not isinstance(self[attr], opt['type']) and self[attr] is not None:
                errors[attr] = f"needs to be of type {opt['type']}{' or None' if not opt['notnone'] else ''}"
        if len(errors) == 0:
            errors = self.validate()
        return errors

    def validate(self):
        return dict()

    def save(self):
        errors = self.validate_base()
        if not len(errors) == 0:
            return {'errors': errors}

        self.save_pre()
        if self['_id'] is None:
            docDB.create(self.__class__.__name__, self._attr)
            result = 'created'
        else:
            docDB.replace(self.__class__.__name__, self._attr)
            result = 'updated'
        self.save_post()

        return {result: self['_id']}

    def save_pre(self):
        pass

    def save_post(self):
        pass

    def delete(self):
        saved_id = self['_id']
        if self['_id'] is not None and docDB.exists(self.__class__.__name__, self['_id']):
            pre_delete_result = self.delete_pre()
            if pre_delete_result is not None and 'error' in pre_delete_result:
                return pre_delete_result
            docDB.delete(self.__class__.__name__, self['_id'])
            self.delete_post()
        self.__init_attr()
        return {'deleted': saved_id}

    def delete_pre(self):
        pass

    def delete_post(self):
        pass

    def reload(self):
        fromdb = docDB.get(self.__class__.__name__, self['_id'])
        if fromdb is not None:
            self._attr = fromdb

    def drop_cache(self):
        self._cache = dict()

    def json(self):
        result = {**{'id': self['_id']}, **self._attr}
        result.pop('_id', None)
        return result
