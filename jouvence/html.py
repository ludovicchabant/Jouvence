"""The ``jouvence.html`` module contains utilities for turning a
Fountain screenplay into a web page, along with other web-related
features.
"""
import os.path
from markupsafe import escape
from .renderer import BaseDocumentRenderer, BaseTextRenderer


def _elem(out, elem_name, class_name, contents):
    f = out.write
    f('<%s' % elem_name)
    if class_name:
        f(' class="jouvence-%s"' % class_name)
    f('>')
    f(contents)
    f('</%s>\n' % elem_name)


def _br(text, strip_first=False):
    lines = text.split('\n')
    if strip_first and lines[0].strip() == '':
        lines = lines[1:]
    return '<br/>\n'.join(lines)


def _res(filename):
    path = os.path.join(os.path.dirname(__file__), 'resources', filename)
    with open(path, 'r') as fp:
        return fp.read()


def get_css():
    """Gets the default CSS screenplay theme that Jouvence uses."""
    return _res('html_styles.css')


class HtmlDocumentRenderer(BaseDocumentRenderer):
    """A document renderer that formats a screenplay into a web page.
    """
    def __init__(self, standalone=True):
        """Creates a new HTML renderer.

            `standalone`
                If ``True`` (the default), it will render a complete HTML
                page, with CSS styling. If ``False``, it will just produce
                the markup for the screenplay itself. The calling
                application is responsible for producing the rest of the
                HTML page, along with CSS code, to render the screenplay
                properly.
        """
        super().__init__(HtmlTextRenderer())
        self.standalone = standalone

    def get_css(self):
        """Gets the default CSS screenplay theme that Jouvence uses.

        This is the same as :func:`~jouvence.html.get_css`.
        """
        return _res('html_styles.css')

    def write_header(self, doc, out):
        if self.standalone:
            meta = doc.title_values.get
            data = {
                # TODO: need a "strip formatting" to have a clean title.
                'title': meta('title', "Fountain Screenplay"),
                'description': meta('description', ''),
                'css': self.get_css()
            }
            out.write(_res('html_header.html') % data)
        out.write('<div class="jouvence-doc">\n')
        out.write('<div class="jouvence-main">\n')

    def write_footer(self, doc, out):
        out.write('</div>\n')  # End `jouvence-main`

        if self.text_renderer.notes:
            out.write('<div class="jouvence-notes">\n')
            self._render_footnotes(out)
            out.write('</div>\n')  # End `jouvence-notes`

        out.write('</div>\n')  # End `jouvence-doc`

        if self.standalone:
            out.write(_res('html_footer.html'))

    def write_title_page(self, values, out):
        out.write('<div class="jouvence-title-page">\n')

        _elem(out, 'h1', None, _br(values['title']))
        _elem(out, 'p', 'title-page-heading', _br(values['credit']))
        _elem(out, 'p', 'title-page-heading', _br(values['author']))

        ddate = values.get('date') or values.get('draft date')
        if ddate:
            _elem(out, 'p', 'title-page-footer', _br(ddate))
        contact = values.get('contact')
        if contact:
            _elem(out, 'p', 'title-page-footer', _br(contact))

        out.write('</div>\n')
        self.write_pagebreak(out)

    def write_scene_heading(self, text, out):
        _elem(out, 'p', 'scene-heading', text)

    def write_action(self, text, out):
        _elem(out, 'p', 'action', _br(text, True))

    def write_centeredaction(self, text, out):
        _elem(out, 'p', 'action-centered', _br(text, True))

    def write_character(self, text, out):
        _elem(out, 'p', 'character', text)

    def write_dialog(self, text, out):
        _elem(out, 'p', 'dialog', _br(text))

    def write_parenthetical(self, text, out):
        _elem(out, 'p', 'parenthetical', text)

    def write_transition(self, text, out):
        _elem(out, 'p', 'transition', text)

    def write_lyrics(self, text, out):
        _elem(out, 'p', 'lyrics', _br(text, True))

    def write_pagebreak(self, out):
        out.write('<hr/>\n')

    def write_section(self, depth, text, out):
        _elem(out, 'p', 'section', '%s %s' % ('#' * depth, text))

    def write_synopsis(self, text, out):
        _elem(out, 'p', 'synopsis', text)

    def _render_footnotes(self, out):
        for i, n in enumerate(self.text_renderer.notes):
            note_id = i + 1
            out.write(
                '<div class="jouvence-note" id="jouvence-note-%d">' %
                note_id)
            text = '<sup>%d</sup> %s' % (note_id, n)
            _elem(out, 'p', None, _br(text))
            out.write('</div>\n')


class HtmlTextRenderer(BaseTextRenderer):
    """A text renderer for producing HTML markup."""
    def __init__(self):
        self.notes = []

    def render_text(self, text):
        return super().render_text(escape(text))

    def make_italics(self, text):
        return '<em>%s</em>' % text

    def make_bold(self, text):
        return '<strong>%s</strong>' % text

    def make_underline(self, text):
        return '<u>%s</u>' % text

    def make_note(self, text):
        note_id = len(self.notes) + 1
        out = '<sup id="jouvence-note-ref-%d">' % note_id
        out += '<a rel="footnote" href="#jouvence-note-%d">' % note_id
        out += str(note_id)
        out += '</a></sup>'
        self.notes.append(text)
        return out
