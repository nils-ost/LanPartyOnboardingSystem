from helpers.docdb import docDB


def get_commited():
    result = docDB.get('system', 'commited')
    if result is None:
        return False
    else:
        return result.get('state', False)


def set_commited(state):
    if not docDB.update('system', 'commited', {'state': state}):
        docDB.create('system', 'commited', {'state': state})


def get_open_commits():
    result = 0
    for s in docDB.search_many('Switch', {'commited': False}):
        result += 1
    return result
