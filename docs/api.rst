
API
===

.. module:: jouvence
   :synopsis: Jouvence API

The Jouvence API is fairly simple, and includes:

   * A Fountain parser that returns a screenplay object.
   * Several renderers, for formatting a screenplay object into something
     you can display on screen or elsewhere.
   * A screenplay object that you can manipulate for custom rendering, 
     analysis, and more.


Parser
------

.. automodule:: jouvence.parser
   :synopsis: The Jouvence parser
   :members:


Document
--------

.. module:: jouvence.document
   :synopsis: The Jouvence document object model


.. autoclass:: JouvenceDocument
   :members:

   .. attribute:: title_values

      The title page key/values dictionary.

   .. attribute:: scenes

      The list of scenes in the screenplay.

      Most screenplays start with some "free text" before the first scene.
      In this case, the first scene would have no header, and would contain
      this text.


.. autoclass:: JouvenceScene
   :members:

   .. attribute:: header

      The header text of the scene, _e.g._ "EXT. JAMES' HOUSE - DAY".

   .. attribute:: paragraphs

      The list of paragraphs in the scene. Each paragraph is an instance
      of :class:`~jouvence.document.JouvenceSceneElement`.

   .. method:: addAction(text)

      Adds an action (paragraph with ``TYPE_ACTION`` type).

   .. method:: addCenteredAction(text)

      Adds a centered action (paragraph with ``TYPE_CENTEREDACTION`` type).

   .. method:: addCharacter(text)

      Adds a character line (paragraph with ``TYPE_CHARACTER`` type).

   .. method:: addDialog(text)

      Adds a dialog line (paragraph with ``TYPE_DIALOG`` type).

   .. method:: addParenthetical(text)

      Adds a parenthetical (paragraph with ``TYPE_PARENTHETICAL`` type).

   .. method:: addTransition(text)

      Adds a transition (paragraph with ``TYPE_TRANSITION`` type).

   .. method:: addLyrics(text)

      Adds some lyrics (paragraph with ``TYPE_LYRICS`` type).

   .. method:: addSynopsis(text)

      Adds a synopsis (paragraph with ``TYPE_SYNOPSIS`` type).


.. autoclass:: JouvenceSceneElement
   :members:

   .. attribute:: type

      The type of this element. Could be any of:

      * ``TYPE_ACTION``
      * ``TYPE_CENTEREDACTION``
      * ``TYPE_CHARACTER``
      * ``TYPE_DIALOG``
      * ``TYPE_PARENTHETICAL``
      * ``TYPE_TRANSITION``
      * ``TYPE_LYRICS``
      * ``TYPE_PAGEBREAK``
      * ``TYPE_SECTION``
      * ``TYPE_SYNOPSIS``

   .. attribute:: text

      The text for this paragraph.


.. autoclass:: JouvenceSceneSection
   :members:
   
   Screenplay sections have their own class because they have a ``depth``
   attribute in addition to a type and text.

   .. attribute:: depth

      The depth, or level, of the section.


Renderers
---------

.. module:: jouvence.renderer

.. autoclass:: BaseDocumentRenderer
   :members:

   .. attribute:: force_title_page

      By default, if there are no title page values in a screenplay, no
      title page will be produced. Set ``force_title_page`` to ``True``
      to force rendering a title page with default/placeholder values.

   .. attribute:: text_renderer
   
      The :class:`~BaseTextRenderer` instance that this document renderer
      is using to handle text.

.. autoclass:: BaseTextRenderer
   :members:


.. automodule:: jouvence.html
   :members: get_css

.. autoclass:: HtmlDocumentRenderer
   :members:

.. autoclass:: HtmlTextRenderer
   :members:


.. automodule:: jouvence.console

.. autoclass:: ConsoleDocumentRenderer
   :members:

.. autoclass:: ConsoleTextRenderer
   :members:
