import pytest
from jouvence.renderer import BaseTextRenderer


class TestTextRenderer(BaseTextRenderer):
    def make_bold(self, text):
        return 'B:' + text + ':B'

    def make_italics(self, text):
        return 'I:' + text + ':I'

    def make_underline(self, text):
        return 'U:' + text + ':U'

    def make_note(self, text):
        return 'N:' + text + ':N'


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
    r = TestTextRenderer()
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
    r = TestTextRenderer()
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
    r = TestTextRenderer()
    out = r.render_text(intext)
    assert out == expected


def test_note():
    r = TestTextRenderer()
    out = r.render_text(
        "This is JACK[[Do we have a better name?]]. He likes movies.")
    expected = "This is JACKN:Do we have a better name?:N. He likes movies."
    assert out == expected


def test_note_with_line_break():
    r = TestTextRenderer()
    out = r.render_text(
        "This is JACK[[Do we have a better name?\n"
        "I think we did]]. He likes movies.")
    expected = ("This is JACKN:Do we have a better name?\n"
                "I think we did:N. He likes movies.")
    assert out == expected


def test_note_multiple():
    r = TestTextRenderer()
    out = r.render_text(
        "This is JACK[[Do we have a better name?]]. "
        "He likes movies[[or plays?]].")
    expected = ("This is JACKN:Do we have a better name?:N. "
                "He likes moviesN:or plays?:N.")
    assert out == expected
