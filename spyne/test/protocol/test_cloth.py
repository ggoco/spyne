
#
# spyne - Copyright (C) Spyne contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

import logging
logger = logging.getLogger(__name__)

import unittest

from lxml import etree
from lxml.builder import E

from spyne import ComplexModel, XmlAttribute, Unicode, Array, Integer
from spyne.protocol.cloth import XmlCloth
from spyne.test import FakeContext
from spyne.util.six import BytesIO


class TestXmlCloth(unittest.TestCase):
    def setUp(self):
        self.ctx = FakeContext()
        self.stream = BytesIO()
        logging.basicConfig(level=logging.DEBUG)

    def _run(self, inst, spid=None, tmpl=None):
        cls = inst.__class__
        if tmpl is None:
            assert spid is not None
            tmpl = etree.fromstring("""<a><b spyne_id="%s"></b></a>""" % spid)
        else:
            assert spid is None

        with etree.xmlfile(self.stream) as parent:
            XmlCloth(tmpl).subserialize(self.ctx, cls, inst, parent)
        elt = etree.fromstring(self.stream.getvalue())
        print etree.tostring(elt, pretty_print=True)
        return elt

    def test_simple_value(self):
        class SomeObject(ComplexModel):
            s = Unicode

        v = 'punk.'
        elt = self._run(SomeObject(s=v), spid='s')

        assert elt[0].text == v

    def test_simple_empty(self):
        class SomeObject(ComplexModel):
            s = Unicode

        elt = self._run(SomeObject(), spid='s')

        assert len(elt) == 0

    def test_simple_empty_nonoptional(self):
        class SomeObject(ComplexModel):
            s = Unicode(min_occurs=1)

        elt = self._run(SomeObject(), spid='s')

        assert elt[0].text is None

    def test_simple_empty_nonoptional_clear(self):
        class SomeObject(ComplexModel):
            s = Unicode(min_occurs=1)

        tmpl = etree.fromstring("""<a><b spyne_id="s">oi punk!</b></a>""")

        elt = self._run(SomeObject(), tmpl=tmpl)

        assert elt[0].text is None

    def test_simple_value_xmlattribute(self):
        v = 'punk.'

        class SomeObject(ComplexModel):
            s = XmlAttribute(Unicode(min_occurs=1))

        tmpl = etree.fromstring("""<a></a>""")
        elt = self._run(SomeObject(s=v), tmpl=tmpl)

        assert elt.attrib['s'] == v

    def test_array(self):
        v = range(3)

        class SomeObject(ComplexModel):
            s = Array(Integer)

        tmpl = E.a(
            E.b(
                E.c(spyne_id="integer"),
                spyne_id="s",
            )
        )

        elt = self._run(SomeObject(s=v), tmpl=tmpl)

        assert elt.xpath('//c/text()') == [str(i) for i in v]

    def test_array_empty(self):
        class SomeObject(ComplexModel):
            s = Array(Integer)

        elt_str = '<a><b spyne_id="s"><c spyne_id="integer"></c></b></a>'
        tmpl = etree.fromstring(elt_str)

        elt = self._run(SomeObject(), tmpl=tmpl)

        assert elt.xpath('//c') == []

    def test_array_empty_nonoptional(self):
        class SomeObject(ComplexModel):
            s = Array(Integer(min_occurs=1))

        elt_str = '<a><b spyne_id="s"><c spyne_id="integer"></c></b></a>'
        tmpl = etree.fromstring(elt_str)

        elt = self._run(SomeObject(), tmpl=tmpl)

        assert elt.xpath('//c') == [tmpl[0][0]]

    def test_simple_two_tags(self):
        class SomeObject(ComplexModel):
            s = Unicode
            i = Integer

        v = SomeObject(s='s', i=5)

        tmpl = E.a(
            E.b1(),
            E.b2(
                E.c1(spyne_id="s"),
                E.c2(),
            ),
            E.e(
                E.g1(),
                E.g2(spyne_id="i"),
                E.g3(),
            ),
        )

        elt = self._run(v, tmpl=tmpl)

        print etree.tostring(elt, pretty_print=True)
        assert elt[0].tag == 'b1'
        assert elt[1].tag == 'b2'
        assert elt[1][0].tag == 'c1'
        assert elt[1][0].text == 's'
        assert elt[1][1].tag == 'c2'
        assert elt[2].tag == 'e'
        assert elt[2][0].tag == 'g1'
        assert elt[2][1].tag == 'g2'
        assert elt[2][1].text == '5'
        assert elt[2][2].tag == 'g3'