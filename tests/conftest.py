import sys
import logging
import yaml
import pytest
from fontaine.document import (
    FontaineSceneElement,
    TYPE_ACTION, TYPE_CHARACTER, TYPE_DIALOG, TYPE_PARENTHETICAL)
from fontaine.parser import FontaineParser, FontaineParserError


def pytest_addoption(parser):
    parser.addoption(
            '--log-debug',
            action='store_true',
            help="Sets the Fontaine logger to output debug info to stdout.")


def pytest_configure(config):
    if config.getoption('--log-debug'):
        hdl = logging.StreamHandler(stream=sys.stdout)
        logging.getLogger('fontaine').addHandler(hdl)
        logging.getLogger('fontaine').setLevel(logging.DEBUG)


def pytest_collect_file(parent, path):
    if path.ext == '.yaml' and path.basename.startswith("test"):
        return FontaineScriptTestFile(path, parent)
    return None


def assert_scenes(actual, scenes):
    assert len(actual) == len(scenes)
    for a, e in zip(actual, scenes):
        assert_scene(a, e[0], e[1:])


def assert_scene(actual, header, paragraphs):
    if header is not None:
        assert actual.header == header
    assert len(actual.paragraphs) == len(paragraphs)
    for a, e in zip(actual.paragraphs, paragraphs):
        assert_paragraph(a, e)


def assert_paragraph(actual, expected):
    if isinstance(expected, str):
        assert isinstance(actual, FontaineSceneElement)
        assert actual.type == TYPE_ACTION
        assert actual.text == expected
    elif isinstance(expected, FontaineSceneElement):
        assert isinstance(actual, FontaineSceneElement)
        assert actual.type == expected.type
        assert actual.text == expected.text
    else:
        raise NotImplementedError("Don't know what this is: %s" % expected)


def _c(name):
    return FontaineSceneElement(TYPE_CHARACTER, name)


def _p(text):
    return FontaineSceneElement(TYPE_PARENTHETICAL, text)


def _d(text):
    return FontaineSceneElement(TYPE_DIALOG, text)


class FontaineScriptTestFile(pytest.File):
    def collect(self):
        spec = yaml.load_all(self.fspath.open(encoding='utf8'))
        for i, item in enumerate(spec):
            name = '%s_%d' % (self.fspath.basename, i)
            if 'test_name' in item:
                name += '_%s' % item['test_name']
            yield FontaineScriptTestItem(name, self, item)


class FontaineScriptTestItem(pytest.Item):
    def __init__(self, name, parent, spec):
        super().__init__(name, parent)
        self.spec = spec

    def reportinfo(self):
        return self.fspath, 0, "fontaine script test: %s" % self.name

    def runtest(self):
        intext = self.spec.get('in')
        expected = self.spec.get('out')
        title = self.spec.get('title')
        if intext is None or expected is None:
            raise Exception("No 'in' or 'out' specified.")

        parser = FontaineParser()
        doc = parser.parseString(intext)
        if title is not None:
            assert title == doc.title_values
        assert_scenes(doc.scenes, make_scenes(expected))

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, FontaineParserError):
            return ('\n'.join(
                ['Parser error:', str(excinfo.value)]))
        return super().repr_failure(excinfo)


def make_scenes(spec):
    if not isinstance(spec, list):
        raise Exception("Script specs must be lists.")

    out = []
    cur_header = None
    cur_paras = []

    for item in spec:
        token = item[:1]
        if token == '.':
            if cur_header or cur_paras:
                out.append([cur_header] + cur_paras)
            cur_header = item[1:]
        elif token == '!':
            cur_paras.append(item[1:])
        elif token == '@':
            cur_paras.append(_c(item[1:]))
        elif token == '=':
            cur_paras.append(_d(item[1:]))
        elif token == '_':
            cur_paras.append(_p(item[1:]))
        else:
            raise Exception("Unknown token: %s" % token)
    if cur_header or cur_paras:
        out.append([cur_header] + cur_paras)
    return out
