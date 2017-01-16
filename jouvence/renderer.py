import re
from jouvence.document import (
    TYPE_ACTION, TYPE_CENTEREDACTION, TYPE_CHARACTER, TYPE_DIALOG,
    TYPE_PARENTHETICAL, TYPE_TRANSITION, TYPE_LYRICS, TYPE_PAGEBREAK,
    TYPE_SECTION, TYPE_SYNOPSIS)


class BaseDocumentRenderer:
    """The base class for document renderers.

    Document renderers are given a document to transform into whatever
    format they're responsible for.
    """
    def __init__(self, text_renderer=None):
        """Initializes the document renderer.

            `text_renderer`
                The :class:`~BaseTextRenderer` instance to use for
                formatting text.
        """
        self.force_title_page = False
        self.text_renderer = text_renderer
        if not text_renderer:
            self.text_renderer = NullTextRenderer()

        self._para_rdrs = {
            TYPE_ACTION: self.write_action,
            TYPE_CENTEREDACTION: self.write_centeredaction,
            TYPE_CHARACTER: self.write_character,
            TYPE_DIALOG: self.write_dialog,
            TYPE_PARENTHETICAL: self.write_parenthetical,
            TYPE_TRANSITION: self.write_transition,
            TYPE_LYRICS: self.write_lyrics,
            TYPE_PAGEBREAK: self.write_pagebreak,
            TYPE_SECTION: self.write_section,
            TYPE_SYNOPSIS: self.write_synopsis,
        }

    def _tr(self, text):
        return self.text_renderer.render_text(text)

    def render_doc(self, doc, out):
        """Renders the given document (``doc``) into the given buffer
        (``out``).

        The output buffer must be a file-like object, like the return
        value of the ``open()`` built-in function, or an instance of
        ``io.StringIO``, among others.
        """
        self.write_header(doc, out)
        self.render_title_page(doc.title_values, out)
        for s in doc.scenes:
            self.render_scene(s, out)
        self.write_footer(doc, out)

    def render_title_page(self, values, out):
        if not self.force_title_page and not values:
            return

        clean_values = values.copy()
        clean_values.setdefault('title', 'Untitled Screenplay')
        clean_values.setdefault('credit', 'Written by')
        clean_values.setdefault('author', 'Unknown')
        for k in clean_values:
            clean_values[k] = self._tr(clean_values[k])
        self.write_title_page(clean_values, out)

    def render_scene(self, scene, out):
        if scene.header is not None:
            self.write_scene_heading(scene.header, out)
        for p in scene.paragraphs:
            rdr_func = self._para_rdrs[p.type]
            if p.type == TYPE_PAGEBREAK:
                rdr_func(out)
            elif p.type == TYPE_SECTION:
                rdr_func(p.depth, self._tr(p.text), out)
            else:
                rdr_func(self._tr(p.text), out)

    def write_header(self, doc, out):
        pass

    def write_footer(self, doc, out):
        pass

    def write_title_page(self, values, out):
        raise NotImplementedError()

    def write_scene_heading(self, text, out):
        raise NotImplementedError()

    def write_action(self, text, out):
        raise NotImplementedError()

    def write_centeredaction(self, text, out):
        raise NotImplementedError()

    def write_character(self, text, out):
        raise NotImplementedError()

    def write_dialog(self, text, out):
        raise NotImplementedError()

    def write_parenthetical(self, text, out):
        raise NotImplementedError()

    def write_transition(self, text, out):
        raise NotImplementedError()

    def write_lyrics(self, text, out):
        raise NotImplementedError()

    def write_pagebreak(self, out):
        raise NotImplementedError()

    def write_section(self, depth, text, out):
        raise NotImplementedError()

    def write_synopsis(self, text, out):
        raise NotImplementedError()


RE_ITALICS = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?\*(?P<text>.*[^\s\*])\*(?=[^a-zA-Z0-9\*]|$)")
RE_BOLD = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?\*\*(?P<text>.*[^\s])\*\*(?=[^a-zA-Z0-9]|$)")
RE_UNDERLINE = re.compile(
    r"(?P<before>^|\s)(?P<esc>\\)?_(?P<text>.*[^\s])_(?=[^a-zA-Z0-9]|$)")

RE_NOTE = re.compile(r"\[\[(?P<text>.+?)\]\]", re.DOTALL)


class BaseTextRenderer:
    """A class responsible for rendering text, including such things as
    italics, bold, or underline.
    """
    def render_text(self, text):
        """Processes the given text, and returns the formatted data."""
        # Replace bold stuff to catch double asterisks.
        text = RE_BOLD.sub(self._do_make_bold, text)
        text = RE_ITALICS.sub(self._do_make_italics, text)
        text = RE_UNDERLINE.sub(self._do_make_underline, text)
        text = RE_NOTE.sub(self._do_make_note, text)

        return text

    def _do_make_italics(self, m):
        if m.group('esc'):
            return m.group('before') + '*' + m.group('text') + '*'
        return (
            m.group('before') +
            self.make_italics(m.group('text')))

    def _do_make_bold(self, m):
        if m.group('esc'):
            return m.group('before') + '**' + m.group('text') + '**'
        return (
            m.group('before') +
            self.make_bold(m.group('text')))

    def _do_make_underline(self, m):
        if m.group('esc'):
            return m.group('before') + '_' + m.group('text') + '_'
        return (
            m.group('before') +
            self.make_underline(m.group('text')))

    def _do_make_note(self, m):
        return self.make_note(m.group('text'))

    def make_italics(self, text):
        raise NotImplementedError()

    def make_bold(self, text):
        raise NotImplementedError()

    def make_underline(self, text):
        raise NotImplementedError()

    def make_note(self, text):
        raise NotImplementedError()


class NullTextRenderer(BaseTextRenderer):
    def make_bold(self, text):
        return text

    def make_italics(self, text):
        return text

    def make_underline(self, text):
        return text

    def make_note(self, text):
        return text
