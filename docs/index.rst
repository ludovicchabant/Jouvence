
.. image:: _static/jouvence.jpg

Jouvence is a Python package for parsing and rendering `Fountain`_ documents.

Jouvence supports:

* Most of the Fountain specification (see limitations below).
* Rendering to HTML and terminals.

The code is available on `BitBucket`_ and `GitHub`_.

.. _fountain: http://fountain.io/
.. _bitbucket: https://bitbucket.org/ludovicchabant/jouvence
.. _github: https://github.com/ludovicchabant/Jouvence


Quickstart
==========

Installation
------------

As with many Python packages, it's recommended that you use `virtualenv`_,
but since Jouvence doesn't have many dependencies, you should be fine.

You can install Jouvence the usual way::

  pip install jouvence

If you want to test that it works, you can feed it a Fountain screenplay and
see if it prints it nicely in your terminal::

  jouvence <path-to-fountain-file>

You should then see the Fountain file rendered with colored and indented
styles.

.. _virtualenv: https://virtualenv.pypa.io/en/stable/


Usage
-----

The Jouvence API goes pretty much like this::

  from jouvence.parser import JouvenceParser
  from jouvence.html import HtmlDocumentRenderer

  parser = JouvenceParser()
  document = parser.parse(path_to_file)
  renderer = HtmlDocumentRenderer()
  with open(path_to_output, 'w') as fp:
    renderer.render_doc(document, fp)



Limitations
-----------

Jouvence doesn't support the complete Fountain syntax yet. The following things
are not implemented:

* Dual dialogue
* Proper Unicode support (although Fountain's spec greatly assumes English screenplays, sadly).



Documentation
=============

.. toctree::
   :maxdepth: 2

   api


If you can't find what you're looking for, have a look here:

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
