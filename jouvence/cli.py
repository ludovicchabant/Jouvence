import sys
import argparse


def main():
    """The Jouvence CLI utility.

    It lets the user print a screenplay to the terminal (with syntax
    highlighting), or save a screenplay into a nicely formatted HTML page.
    """
    parser = argparse.ArgumentParser(
        description='Jouvence command line utility')
    parser.add_argument('script')
    parser.add_argument('out_file', nargs='?')
    args = parser.parse_args()

    from jouvence.parser import JouvenceParser
    p = JouvenceParser()
    doc = p.parse(args.script)

    if not args.out_file:
        from jouvence.console import ConsoleDocumentRenderer
        rdr = ConsoleDocumentRenderer()
        rdr.render_doc(doc, sys.stdout)
    else:
        from jouvence.html import HtmlDocumentRenderer
        rdr = HtmlDocumentRenderer()
        with open(args.out_file, 'w') as fp:
            rdr.render_doc(doc, fp)
