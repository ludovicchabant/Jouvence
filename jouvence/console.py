"""The ``jouvence.console`` module contains utilities for rendering
a Foutain screenplay in a terminal.
"""
import os
import colorama
from .renderer import BaseDocumentRenderer, BaseTextRenderer


def _w(out, style, text, reset_all=False):
    f = out.write
    f(style)
    f(text)
    if not reset_all:
        f(colorama.Style.NORMAL)
    else:
        f(colorama.Style.RESET_ALL)
    f(os.linesep)


class ConsoleDocumentRenderer(BaseDocumentRenderer):
    """A document renderer that prints a screenplay into a terminal with
    some nice syntax highlighting.
    """
    def __init__(self, width=80):
        super().__init__(ConsoleTextRenderer())
        self.width = width
        colorama.init()

    def write_title_page(self, values, out):
        known = ['title', 'credit', 'author', 'authors', 'source']
        center_values = [values.get(i) for i in known]

        print("", file=out)
        for val in center_values:
            if val is not None:
                for l in val.split('\n'):
                    print(l.center(self.width), file=out)
            print("", file=out)
        print("", file=out)
        print("", file=out)

        known = ['date', 'draft date', 'contact', 'copyright']
        bottom_lines = [values.get(i) for i in known]

        _w(out, colorama.Style.DIM, '\n\n'.join([
            b for b in bottom_lines if b is not None]))
        print("", file=out)
        _w(out, colorama.Style.DIM, 80 * '=')

    def write_scene_heading(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.WHITE + colorama.Style.BRIGHT, text, True)

    def write_action(self, text, out):
        print(text, file=out)

    def write_centeredaction(self, text, out):
        print("", file=out)
        for line in text.split('\n'):
            print(line.center(self.width), file=out)

    def write_character(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.WHITE, "\t\t\t" + text, True)

    def write_dialog(self, text, out):
        for line in text.split('\n'):
            print("\t" + line, file=out)

    def write_parenthetical(self, text, out):
        for line in text.split('\n'):
            print("\t\t" + line, file=out)

    def write_transition(self, text, out):
        print("", file=out)
        print("\t\t\t\t" + text, file=out)

    def write_lyrics(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.MAGENTA, text, True)

    def write_pagebreak(self, out):
        print("", file=out)
        _w(out, colorama.Style.DIM, 80 * '=')

    def write_section(self, depth, text, out):
        print("", file=out)
        _w(out, colorama.Fore.CYAN, '#' * depth + ' ' + text, True)

    def write_synopsis(self, text, out):
        print("", file=out)
        _w(out, colorama.Fore.GREEN, '= ' + text, True)


class ConsoleTextRenderer(BaseTextRenderer):
    """A text renderer for producing ANSI colouring."""
    def _writeStyled(self, style, text):
        return style + text + colorama.Style.NORMAL

    def make_italics(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_bold(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_underline(self, text):
        return self._writeStyled(colorama.Style.BRIGHT, text)

    def make_note(self, text):
        out = colorama.Style.DIM + colorama.Fore.MAGENTA
        out += ' [[ ' + text + ' ]] '
        out += colorama.Style.RESET_ALL
        return out
