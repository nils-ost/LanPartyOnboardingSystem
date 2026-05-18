import json


def responseToJson(r):
    r = r.replace("'", '').replace('[]', '###EMPTYBRACKET1###').replace('{}', '###EMPTYBRACKET2###')
    r = r.replace('{', '{"').replace('}', '"}').replace('[', '["').replace(']', '"]').replace(':', '":"').replace(',', '","')
    r = r.replace(':"[', ':[').replace('["[', '[[').replace(']"]', ']]').replace('{"{', '{{').replace('}"}', '}}')
    r = r.replace('{"[', '{[').replace(']"}', ']}').replace('["{', '[{').replace('}"]', '}]')
    r = r.replace(']",', '],').replace(',"[', ',[').replace('}",', '},').replace(',"{', ',{')
    r = r.replace('###EMPTYBRACKET1###', '[]').replace('###EMPTYBRACKET2###', '{}')
    return json.loads(r)


def jsonToRequest(j):
    r = json.dumps(j).replace('\n', '').replace(' ', '').replace('"', '')
    return r


def asciiToStr(a):
    if a is None:
        return ''
    r = ''
    for idx in range(0, len(a), 2):
        r += chr(int(a[idx:idx + 2], 16))
    return r


def strToAscii(s):
    if s is None:
        return ''
    r = ''
    for o in [ord(c) for c in s]:
        h = hex(o).replace('0x', '')
        if len(h) == 1:
            h = '0' + h
        r += h
    return r


def translateKeys(j, tmap, ommit_surplus=False):
    """
    takes a json and translates all keys found in tmap-keys to tmap-value (replaces key names)
    if ommit_surplus is set, only translated keys find their way into the resulting dict
    """
    if isinstance(j, list):
        r = list()
        for e in j:
            r.append(translateKeys(e, tmap, ommit_surplus))
        return r
    elif isinstance(j, dict):
        r = dict()
        for k, v in j.items():
            translated = False
            if k in tmap:
                k = tmap[k]
                translated = True
            if not ommit_surplus or translated:
                r[k] = translateKeys(v, tmap, ommit_surplus)
        return r
    else:
        return j


def jsonAllAsciiToStr(j):
    """
    Helper for development to just try to convert everything in a json from ascii to str
    (to find interesting ascii coded variables)
    """
    r = dict()
    for k, v in j.items():
        if isinstance(v, str):
            try:
                r[k] = asciiToStr(v)
            except Exception:
                r[k] = v
        else:
            r[k] = v
    return r


def jsonAllHexToInt(j):
    """
    Helper for development to just try to convert everything in a json from hex to int
    (to find interesting numeric variables)
    """
    r = dict()
    for k, v in j.items():
        if isinstance(v, list):
            r[k] = list()
            for e in v:
                try:
                    r[k].append(int(e, 16))
                except Exception:
                    r[k].append(e)
        else:
            try:
                r[k] = int(v, 16)
            except Exception:
                r[k] = v
    return r
