"""
Module doc.
"""
import io


class Error(Exception):
    "Recjar exception class."
    pass


class Recjar:
    """Recjar class."""

    _FIELD = 0
    _COMMENT = 1
    _SEPARATOR = 2
    _BLANK_LINE = 3
    _EOF = 4

    def __init__(self):
        self.data = []
        self._stream = None
        self._streamname = None
        self._lineno = None
        self._buf = None

    def nrecords(self):
        "Returns the number of records."
        return sum(1 for rec in self.data if isinstance(rec, list))

    def _fmt(self, message):
        return '%s:%d: %s' % (self._streamname, self._lineno, message)

    def set_of_fieldnames(self):
        "Returns the set of field names."
        return set(field[0] for rec in self.data
                   if isinstance(rec, list) for field in rec)

    def read(self, src):
        "Reads recjar from a file or an open stream."
        if isinstance(src, str):
            self.read_from_file(src)
        else:
            self.read_from_stream(src)

    def read_from_stream(self, stream):
        "Reads recjar from an open stream."
        assert isinstance(stream, io.TextIOBase)
        self._stream = stream
        try:
            self._streamname = stream.name
        except AttributeError:
            self._streamname = 'unnamed stream'
        self._build()

    def read_from_file(self, path):
        "Reads recjar from a file."
        with open(path, encoding="utf-8") as stream:
            self.read_from_stream(stream)

    def write_to_stream(self, stream):
        """Writes recjar to an open stream."""
        for rec in self.data:
            if isinstance(rec, str):
                if rec:
                    stream.write("".join(('%%', rec, '\n')))
                else:
                    stream.write('%%\n')
            else:
                for field in rec:
                    if field[1]:
                        stream.write("".join(
                            (field[0], ': ', field[1], '\n')))
                    else:
                        stream.write("".join((field[0], ':\n')))

    def write_to_file(self, path):
        """Writes recjar to a file."""
        with open(path, 'w', encoding="utf-8") as stream:
            self.write_to_stream(stream)

    @staticmethod
    def isvalid(fieldname):
        """Returns True iff fieldname is a valid field name. Regular
        expression matching correct field names: [A-Za-z][A-Za-z_-]*
        """
        if not fieldname:
            return False
        c = fieldname[0]
        if (c < 'a' or c > 'z') and (c < 'A' or c > 'Z'):
            return False
        if any((c < 'a' or c > 'z') and
               (c < 'A' or c > 'Z') and
               (c < '0' or c > '9') and
               c != '_' and c != '-' for c in fieldname[1:]):
            return False
        return True

    def _split_line(self, field):
        """Splits line into (fieldname, fieldvalue)."""
        pos = field.find(':')
        if pos < 0:
            raise Error(self._fmt('no colon found'))
        fieldname = field[0:pos].rstrip()
        if not self.isvalid(fieldname):
            raise Error(self._fmt('invalid field name'))
        fieldvalue = field[pos + 1:].strip()
        return fieldname, fieldvalue

    def _getline(self):
        """Returns the next line from the input stream and increases
        line counter."""
        try:
            line = self._stream.readline()
        except UnicodeDecodeError:
            raise Error(self._fmt('invalid UTF-8 character'))
        self._lineno += 1
        return line

    def _gettoken(self):
        """Get next token from the stream."""
        if self._buf is None:
            line = self._getline()
        else:
            line = self._buf
            self._buf = None

        if line == '':
            return (self._EOF,)
        line = line.rstrip()
        if line == '':
            return (self._BLANK_LINE,)
        elif line[0] == '#':
            return (self._COMMENT, line[1:].lstrip())
        elif line[0:2] == '%%':
            return (self._SEPARATOR, line[2:])
        else:
            fieldname, fieldvalue = self._split_line(line)
            while True:
                while fieldvalue.endswith('\\'):
                    fieldvalue = fieldvalue[:-1]
                    line = self._getline()
                    if line == '':
                        raise Error(
                            self._fmt('continuation expected'))
                    fieldvalue = fieldvalue + line.strip()
                line = self._getline()
                if line.startswith(' '):
                    fieldvalue = fieldvalue + ' ' + line.strip() \
                                 if fieldvalue else line.strip()
                else:
                    self._buf = line
                    break
            return (self._FIELD, fieldname, fieldvalue)

    def _build(self):
        """Build data."""
        self.data = []
        self._lineno = 0
        self._buf = None
        rec = []
        while True:
            token = self._gettoken()
            if token[0] == self._EOF:
                break
            elif token[0] == self._COMMENT:
                pass
            elif token[0] == self._BLANK_LINE:
                pass
            elif token[0] == self._FIELD:
                rec.append((token[1], token[2]))
            elif token[0] == self._SEPARATOR:
                if len(rec) > 0:
                    self.data.append(rec)
                    rec = []
                self.data.append(token[1])
            else:
                assert False, 'invalid token'
        if len(rec) > 0:
            self.data.append(rec)


class Recset:
    """Recset class."""

    def __init__(self):
        self.name = ''
        self.allowed = set()
        self.mandatory = set()
        self.unique = set()
        self.key = None
        self.prohibited = set()
        self.data = []

    def _read_from_recjar(self, rjar, first, last, name):
        assert isinstance(name, str)
        assert first < last
        self.name = name if name != "" else "Unnamed"
        rjar = rjar.data
        i = first + 1
        while True:
            if i >= last:
                break
            if isinstance(rjar[i], list):
                break
            assert isinstance(rjar[i], str)
            s = rjar[i]
            if s.startswith('%allowed:'):
                z = s[9:].split()
                if len(z) == 0:
                    raise Error('empty allowed list')
                for f in z:
                    if not Recjar.isvalid(f):
                        raise Error(
                            'invalid field name in allowed list: ' +
                            f)
                self.allowed.update(z)
            elif s.startswith('%mandatory:'):
                z = s[11:].split()
                if len(z) == 0:
                    raise Error('empty mandatory list')
                for f in z:
                    if not Recjar.isvalid(f):
                        raise Error(
                            'invalid field name in mandatory list')
                self.mandatory.update(z)
            elif s.startswith('%unique:'):
                z = s[8:].split()
                if len(z) == 0:
                    raise Error('empty unique list')
                for f in z:
                    if not Recjar.isvalid(f):
                        raise Error(
                            'invalid field name in unique list')
                self.unique.update(z)
            elif s.startswith('%key:'):
                if self.key is not None:
                    raise Error('duplicated key')
                f = s[5:].strip()
                if not Recjar.isvalid(f):
                    raise Error('invalid field name as key: ' + f)
                self.key = f
            elif s.startswith('%prohibited:'):
                z = s[12:].split()
                if len(z) == 0:
                    raise Error('empty prohibited list')
                for f in z:
                    if not Recjar.isvalid(f):
                        raise Error(
                            'invalid field name in prohibited list')
                self.prohibited.update(z)
            i += 1
        while True:
            if i >= last:
                break
            if isinstance(rjar[i], list):
                self.addrec(rjar[i])
            i += 1
        self.check()

    def check(self):
        """Check the set. Should be called after any change into
        the set.
        """
        if len(self.allowed) > 0:
            allfields = self.allowed | self.mandatory
            if self.key is not None:
                allfields.add(self.key)
            for r in self.data:
                for f in r:
                    if f not in allfields:
                        raise Error('field ' + f + ' not allowed')
        if self.key is not None:
            f = self.key
            set_of_keys = set()
            for r in self.data:
                if f not in r:
                    raise Error('no key found')
                if not isinstance(r[f], str):
                    raise Error('two fields with key found')
                if r[f] in set_of_keys:
                    raise Error('duplicated key found')
                set_of_keys.add(r[f])
        for r in self.data:
            for f in self.mandatory:
                if f not in r:
                    raise Error('mandatory field ' + f + ' not found')
            for f in self.unique:
                if f in r and not isinstance(r[f], str):
                    raise Error('unique field ' + f + ' found twice')
            for f in r:
                if f in self.prohibited:
                    raise Error('prohibited field ' + f + ' found')

    def addrec(self, rec):
        "Add one record."
        d = {}
        for f in rec:
            k = f[0]
            if k in d:
                if isinstance(d[k], list):
                    d[k].append(f[1])
                else:
                    assert isinstance(d[k], str)
                    d[k] = [d[k], f[1]]
            else:
                d[k] = f[1]
        self.data.append(d)

    @staticmethod
    def read(src):
        """Returns a list of recsets found in the recjar src.
        src may be a path to file or a stream."""

        def read():
            """Creates the recset."""
            if nrec > 0:
                rset = Recset()
                rset._read_from_recjar(rjar, first, i, name)
                recsets.append(rset)

        rjar = Recjar()
        rjar.read(src)
        recsets = []
        i = 0
        first = 0
        nrec = 0
        name = ''
        while i < len(rjar.data):
            s = rjar.data[i]
            if isinstance(s, list):
                nrec += 1
            elif s.startswith('%rec:'):
                read()
                first = i
                nrec = 0
                if not Recjar.isvalid(s[6:]):
                    raise Error('invalid rec name: ' + s[6:])
                name = s[6:]
            i += 1
        read()
        return recsets
