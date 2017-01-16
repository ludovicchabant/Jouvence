# -*- coding: utf-8 -*-
"""
    JOUVENCE
    ========

    `Fountain`_ is a plain text markup language for screenwriting. Jouvence
    is a Python package for parsing and rendering Fountain documents.

    Jouvence supports:

    * Most of the Fountain specification (see limitations below).
    * Rendering to HTML and terminals.

    .. _fountain: http://fountain.io/

    :copyright: (c) 2017, BOLT80.
    :license: Apache2. See LICENSE file for details.
"""

__docformat__ = 'restructuredtext en'

try:
    from .version import version
except ImportError:
    version = '<unknown>'

__version__ = version
