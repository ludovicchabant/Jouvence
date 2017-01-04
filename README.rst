
########
FONTAINE
########


`Fountain`_ is a plain text markup language for screenwriting. Fontaine
is a Python package for parsing and rendering Fountain documents.

Fontaine supports:

* Most of the Fountain specification (see limitations below).
* Rendering to HTML and terminals.

.. _fountain: http://fountain.io/


Installation
============

As with many Python packages, it's recommended that you use `virtualenv`_,
but since Fontaine doesn't have many dependencies, you should be fine.

You can install Fontaine the usual way::

  pip install fontaine

If you want to test that it works, you can feed it a Fountain screenplay and
see if it prints it nicely in your terminal::

  fontaine <path-to-fountain-file>

You should then see the Fountain file rendered with colored and indented
styles.

.. _virtualenv: https://virtualenv.pypa.io/en/stable/


Usage
=====

The Fontaine API goes pretty much like this::

  from fontaine.parser import FontaineParser
  from fontaine.html import HtmlDocumentRenderer

  parser = FontaineParser()
  document = parser.parse(path_to_file)
  renderer = HtmlDocumentRenderer()
  markup = renderer.render_doc(document)
  return markup


Limitations
===========

Fontaine doesn't support the complete Fountain syntax yet. The following things
are not implemented yet:

* Dual dialogue
* Notes
* Boneyards
* Sections and synopses


