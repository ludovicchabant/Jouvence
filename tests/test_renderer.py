import pytest
from fontaine.renderer import BaseRenderer


class TestRenderer(BaseRenderer):
    def write_bold(self, text):
        return 'B:' + text + ':B'

    def write_italics(self, text):
        return 'I:' + text + ':I'

    def write_underline(self, text):
        return 'U:' + text + ':U'


@pytest.mark.parametrize('intext, expected', [
    ("_Underline_", "U:Underline:U"),
    ("Here's an _underline_.", "Here's an U:underline:U."),
    ("Here's an _underline_ too", "Here's an U:underline:U too"),
    ("This is not_underline_", "This is not_underline_"),
    ("This is not _underline_either", "This is not _underline_either"),
    ("This is _two underlined_ words.", "This is U:two underlined:U words."),
    ("This is _three underlined words_.",
     "This is U:three underlined words:U."),
    ("This is an \_escaped_ one.", "This is an _escaped_ one.")
])
def test_underline(intext, expected):
    r = TestRenderer()
    out = r.render_text(intext)
    assert out == expected


@pytest.mark.parametrize('intext, expected', [
    ("*Italics*", "I:Italics:I"),
    ("Here's some *italics*.", "Here's some I:italics:I."),
    ("Here's some *italics* too", "Here's some I:italics:I too"),
    ("This is not*italics*", "This is not*italics*"),
    ("This is not *italics*either", "This is not *italics*either"),
    ("This is *two italics* words.", "This is I:two italics:I words."),
    ("This is *three italics words*.",
     "This is I:three italics words:I."),
    ("This is some \*escaped* one.", "This is some *escaped* one.")
])
def test_italics(intext, expected):
    r = TestRenderer()
    out = r.render_text(intext)
    assert out == expected


@pytest.mark.parametrize('intext, expected', [
    ("**Bold**", "B:Bold:B"),
    ("Here's some **bold**.", "Here's some B:bold:B."),
    ("Here's some **bold** too", "Here's some B:bold:B too"),
    ("This is not**bold**", "This is not**bold**"),
    ("This is not **bold**either", "This is not **bold**either"),
    ("This is **two bold** words.", "This is B:two bold:B words."),
    ("This is **three bold words**.",
     "This is B:three bold words:B."),
    ("This is some \**escaped** one.", "This is some **escaped** one.")
])
def test_bold(intext, expected):
    r = TestRenderer()
    out = r.render_text(intext)
    assert out == expected