#!/usr/bin/python3

"Tests the module recfile."

import unittest
import io
import os
import filecmp
from recfile import Recjar
from recfile import Recset
import recfile

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(TEST_DIR, 'testdata')


def path(fname):
    "Returns absolute path to test data file."
    return os.path.join(LOCATION, fname)


class TestRecjar(unittest.TestCase):
    "Tests Recjar."

    @staticmethod
    def fromstring(line):
        "Returns a Recjar read from the string."
        rjar = recfile.Recjar()
        rjar.read_from_stream(io.StringIO(line))
        return rjar

    def test01(self):
        "Tests Recjar.isvalid()."
        for fname in ['a', 'A', 'Alpha_beta-gamma', 'a_', 'a-']:
            self.assertTrue(Recjar.isvalid(fname))
        for fname in ['', ' a', 'a ', ':', '_', '-', '_a', '-a']:
            self.assertFalse(Recjar.isvalid(fname))

    def test02(self):
        "Basic test of public methods."
        rjar = Recjar()
        rjar.read_from_file(path('planets.txt'))
        self.assertEqual(rjar.data, [
            [('Planet', 'Mercury'),
             ('Orbital-Radius', '57,910,000 km'),
             ('Diameter', '4,880 km'),
             ('Mass', '3.30e23 kg')],
            '',
            [('Planet', 'Venus'),
             ('Orbital-Radius', '108,200,000 km'),
             ('Diameter', '12,103.6 km'),
             ('Mass', '4.869e24 kg')],
            '',
            [('Planet', 'Earth'),
             ('Orbital-Radius', '149,600,000 km'),
             ('Diameter', '12,756.3 km'),
             ('Mass', '5.972e24 kg'), ('Moons', 'Luna')]])
        self.assertEqual(rjar.nrecords(), 3)
        self.assertEqual(rjar.set_of_fieldnames(),
                         {'Diameter', 'Moons', 'Mass', 'Planet',
                          'Orbital-Radius'})
        rjar.write_to_file(path('planets.out'))
        self.assertTrue(
            filecmp.cmp(path('planets.txt'),
                        path('planets.out'), False))
        os.remove(path('planets.out'))

        rjar.read_from_file(path('planets1.txt'))
        self.assertEqual(rjar.data, [
            ' To jest pierwszy rekord.',
            [('Planeta', 'Merkury'),
             ('Promien_orbity', '57 910 000 km'),
             ('Srednica', '4 880 km'),
             ('Masa', '3,30e23 kg')],
            ' To jest drugi rekord.',
            [('Planeta', 'Wenus'),
             ('Promien_orbity', '108 200 000 km'),
             ('Srednica', '12 103,6 km'),
             ('Masa', '4,869e24 kg')],
            ' To jest trzeci rekord.',
            [('Planeta', 'Ziemia'),
             ('Promien_orbity', '149 600 000 km'),
             ('Srednica', '12 756,3 km'),
             ('Masa', '5,972e24 kg'),
             ('Ksiezyce', 'Ksi\u0119\u017cyc')],
            ' To jest koniec pliku.'])
        self.assertEqual(rjar.nrecords(), 3)
        self.assertEqual(rjar.set_of_fieldnames(),
                         {'Promien_orbity', 'Planeta',
                          'Masa', 'Ksiezyce', 'Srednica'})
        rjar.write_to_file(path('planets1.out'))
        self.assertTrue(
            filecmp.cmp(path('planets1.txt'),
                        path('planets1.out'), False))
        os.remove(path('planets1.out'))

        self.assertRaisesRegex(
            recfile.Error,
            'planets2.txt:0: invalid UTF-8 character',
            rjar.read_from_file,
            path('planets2.txt'))

    def test03(self):
        "Testing multi-line fields and extra white space."
        cases1 = (
            ('Planet:Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet: Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet : Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet  : Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:  Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:   Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet :  Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\\\nMercury\n', [[('Planet', 'Mercury')]]),
            ('Planet: \\\nMercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:  \\\nMercury\n', [[('Planet', 'Mercury')]]),
            ('Planet: \\\nM\\\nercury\n', [[('Planet', 'Mercury')]]),
            ('Planet: \\\nM\\\n\\\nercury\n',
             [[('Planet', 'Mercury')]]),
            ('Planet: \\\nM\\\n\\\ne\\\nrc\\\nury\n',
             [[('Planet', 'Mercury')]]),
            ('Planet:\n Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\n  Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\n   Mercury\n', [[('Planet', 'Mercury')]]),
            ('Planet: M\n ercury\n', [[('Planet', 'M ercury')]]),
            ('Planet: M\n  ercury\n', [[('Planet', 'M ercury')]]),
            ('Planet: M\n   ercury\n', [[('Planet', 'M ercury')]]),
            ('Planet: Me\n rcury\n', [[('Planet', 'Me rcury')]]),
            ('Planet: Me\n  rcury\n', [[('Planet', 'Me rcury')]]),
            ('Planet: Me\n   rcury\n', [[('Planet', 'Me rcury')]]),
            ('Planet:\n M\\\nercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\n M\\\n ercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\n M\\\n  ercury\n', [[('Planet', 'Mercury')]]),
            ('Planet:\n M \\\nercury\n', [[('Planet', 'M ercury')]]),
            ('Planet:\n M  \\\n ercury\n',
             [[('Planet', 'M  ercury')]]),
            ('Planet:\n M   \\\n  ercury\n',
             [[('Planet', 'M   ercury')]]),
            ('Planet:\n M\\\n\n ercury\n',
             [[('Planet', 'M ercury')]]),
            ('Planet:\n M\\\n\n  ercury\n',
             [[('Planet', 'M ercury')]]),
            ('Planet: M\\\ne\\\nrc\\\nury\n',
             [[('Planet', 'Mercury')]]),
            ('Planet: M\n e\\\n\\\n\n r\\\n\\\n\\\n c\n ury\n',
             [[('Planet', 'M e rc ury')]]),
        )
        cases2 = [
            ('Planet Mercury\n',
             'unnamed stream:1: no colon found'),
            ('Plane&t: Mercury\n',
             'unnamed stream:1: invalid field name'),
            ("!: Mercury\n",
             'unnamed stream:1: invalid field name'),
            (": Mercury\n",
             'unnamed stream:1: invalid field name'),
            (" : Mercury\n",
             'unnamed stream:1: invalid field name'),
            ("Planet: Mercury\\\\\n",
             'unnamed stream:2: continuation expected')
        ]
        for inp, out in cases1:
            with self.subTest(out):
                rjar = self.fromstring(inp)
                self.assertEqual(rjar.data, out)
        for inp, msg in cases2:
            with self.subTest(msg):
                self.assertRaisesRegex(
                    recfile.Error,
                    msg,
                    self.fromstring,
                    inp)


class TestRecset(unittest.TestCase):
    "Tests Recset."

    def test01(self):
        "Basic test."
        recsets = Recset.read(path('misc.txt'))
        self.assertEqual(len(recsets), 4)
        rset = recsets[0]
        self.assertEqual(rset.name, "Unnamed")
        self.assertEqual(rset.allowed, set())
        self.assertEqual(rset.mandatory, set())
        self.assertEqual(rset.unique, set())
        self.assertIsNone(rset.key)
        self.assertEqual(rset.prohibited, set())
        self.assertEqual(rset.data,
                         [{'Date': '2017-10-11',
                           'Note': 'The number is invalid.',
                           'Number': '1711.3'}])

        rset = recsets[1]
        self.assertEqual(rset.name, "Book")
        self.assertEqual(rset.allowed,
                         {'Publisher', 'Author', 'Year',
                          'Title', 'ISBN'})
        self.assertEqual(rset.mandatory,
                         {'Publisher', 'Author', 'Year',
                          'Title', 'ISBN'})
        self.assertEqual(rset.unique,
                         {'Publisher', 'Year', 'Title', 'ISBN'})
        self.assertIsNone(rset.key)
        self.assertEqual(rset.prohibited, set())
        self.assertEqual(
            rset.data,
            [{'Publisher': 'Cambridge University Press',
              'Author': ['Anatole Katok', 'Boris Hasselblatt'],
              'Title': 'Introduction to the modern theory'
                       ' of dynamical systems',
              'Year': '1999',
              'ISBN': '9780521575577'},
             {'Publisher': 'Springer',
              'Author': ['David Cox', 'John Little', "Donal O'Shea"],
              'Title': 'Ideals, varieties, and algorithms',
              'Year': '2007',
              'ISBN': '9780387356501'},
             {'Publisher': 'Dover Publications',
              'Author': ['K. B. Athreya', 'P. E. Ney'],
              'Title': 'Branching processes',
              'Year': '2004',
              'ISBN': '0486434745'}])

        rset = recsets[2]
        self.assertEqual(rset.name, "Article")
        self.assertEqual(rset.allowed, set())
        self.assertEqual(rset.mandatory, set())
        self.assertEqual(rset.unique, set())
        self.assertIsNone(rset.key)
        self.assertEqual(rset.prohibited, set())
        self.assertEqual(
            rset.data,
            [{'Volume': '88',
              'Journal': 'Physical Review Letters',
              'Author': 'Christoph Bandt, Bernd Pompe',
              'Title': 'Permutation Entropy: A Natural Complexity'
                       ' Measure for Time Series',
              'Year': '2002'},
             {'Volume': '37',
              'Journal': 'Biometrika',
              'Author': 'J. Durbin, G. S. Watson',
              'Title': 'Testing for serial correlation in least'
                       ' squares regression. I',
              'Pages': '409-428',
              'Year': '1950'},
             {'Volume': '13',
              'Journal': 'Communications of the ACM',
              'Author': 'Jay Earley',
              'Title': 'An efficient context-free parsing algorithm',
              'Year': '1970'}])
        rset = recsets[3]
        self.assertEqual(rset.name, "Film")
        self.assertEqual(rset.allowed, set())
        self.assertEqual(rset.mandatory, set())
        self.assertEqual(rset.unique, set())
        self.assertIsNone(rset.key)
        self.assertEqual(rset.prohibited, set())
        self.assertEqual(
            rset.data,
            [{'Year': '1975',
              'Title': 'Noce i dnie',
              'Director': 'Jerzy Antczak'},
             {'Year': '1990',
              'Title': 'Korczak',
              'Director': 'Andrzej Wajda'},
             {'Year': '1978',
              'Title': 'Zmory',
              'Director':
              'Wojciech Marczewski'}])
        print('\n')
#       for i in recsets:
#           print(i.name)
#           print(i.allowed)
#           print(i.mandatory)
#           print(i.unique)
#           print(i.key)
#           print(i.prohibited)
#           print(i.data)
#       print('\n')

    @staticmethod
    def fromstring(lines):
        "Returns a list of recsets read from the string."
        return Recset.read(io.StringIO(lines))

    def test02(self):
        "Test incorrect input."
        cases = [
            ("%%%rec: Book\n%%%key: Number No\nNumber: 1\nNo: 2\n",
             "invalid field name as key: Number No"),
            ("%%%rec: Book\n%%%key: Number\n%%%key: No\n"
             "Number: 1\nNo: 2\n",
             "duplicated key"),
            ("%%%rec: Book\n%%%allowed:\nAuthor:\n",
             "empty allowed list"),
            ("%%%rec: Book\n%%%allowed: _a\nAuthor:\n",
             "invalid field name in allowed list: _a"),
            ("%%%rec: Book\n%%%allowed: Author\nNumber: 1\n",
             "field Number not allowed"),
            ("%%%rec: Book\n%%%key: Number\nAuthor:\nTitle:\n",
             "no key found"),
            ("%%%rec: Book\n%%%key: Number\nNumber: 1\nAuthor:\n"
             "Title:\nNumber: 2\n",
             "two fields with key found"),
            ("%%%rec: Book\n%%%key: Number\n"
             "Number: 1\nAuthor:\nTitle:\n"
             "%%\n"
             "Number: 2\nAuthor:\nTitle:\n"
             "%%\n"
             "Number: 1\nAuthor:\nTitle:\n",
             "duplicated key found"),
            ("%%%rec: Book\n%%%mandatory: Author Title\n"
             "Author1:\nTitle:\n",
             "mandatory field Author not found"),
            ("%%%rec: Book\n%%%unique: Title\n"
             "Title:\nAuthor:\nTitle:\n",
             "unique field Title found twice"),
            ("%%%rec: Book\n%%%prohibited: Journal\n"
             "Author:\nTitle:\nJournal:\n",
             "prohibited field Journal found")
        ]

        for src, msg in cases:
            with self.subTest(msg):
                self.assertRaisesRegex(
                    recfile.Error,
                    msg,
                    self.fromstring,
                    src)

if __name__ == '__main__':
    unittest.main()
