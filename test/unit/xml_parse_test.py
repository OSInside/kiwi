import pytest
from kiwi.xml_parse import quote_xml_aux, quote_attrib, quote_python


@pytest.mark.parametrize("string,result", [
    ("hallo", "hallo"),
    ("a & b", "a &amp; b"),
    ("a < b", "a &lt; b"),
    ("a > b", "a &gt; b"),
    ("a ' b", "a ' b"),
    ('a " b', 'a " b'),
    ('a < b > c == "abc" + \'edf\'',
     'a &lt; b &gt; c == "abc" + \'edf\''),
    ("a < b > c == 'abc' + \"edf\"",
     'a &lt; b &gt; c == \'abc\' + "edf"')
])
def test_quote_xml_aux(string, result):
    assert quote_xml_aux(string) == result


@pytest.mark.parametrize("string,result", [
    ("hallo", '"hallo"'),
    ("a & b", '"a &amp; b"'),
    ("a < b", '"a &lt; b"'),
    ("a > b", '"a &gt; b"'),
    ("a ' b", '"a \' b"'),
    ('a "b" c', '\'a "b" c\''),
    ('a < b > c == "abc" + \'edf\'',
     '"a &lt; b &gt; c == &quot;abc&quot; + \'edf\'"'),
])
def test_quote_attrib(string, result):
    assert quote_attrib(string) == result


@pytest.mark.parametrize("string,result", [
    ("a 'b' c", '"a \'b\' c"'),
    ("""a "b" c""", '\'a "b" c\''),
    ('''a 'b' c''', '"a \'b\' c"'),
    # ('''a 'b' "c" d''',
    #  '\'a \\\'b\\\' "c" d\'' # the new implementation
    #  '"a \'b\' \\"c\\" d"'), # the old implementation
])
def test_quote_python(string, result):
    assert quote_python(string) == result
