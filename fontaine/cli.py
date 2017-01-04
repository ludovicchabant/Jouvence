import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Fontaine command line utility')
    parser.add_argument('script')
    parser.add_argument('out_file', nargs='?')
    args = parser.parse_args()

    from fontaine.parser import FontaineParser
    p = FontaineParser()
    doc = p.parse(args.script)

    if not args.out_file:
        from fontaine.console import ConsoleDocumentRenderer
        rdr = ConsoleDocumentRenderer()
        rdr.render_doc(doc, sys.stdout)
    else:
        from fontaine.html import HtmlDocumentRenderer
        rdr = HtmlDocumentRenderer()
        with open(args.out_file, 'w') as fp:
            rdr.render_doc(doc, fp)
