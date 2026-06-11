Change Log
##########

..
   All enhancements and patches to xblocks-contrib will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
**********

0.17.0 - 2026-06-11

Changed
=======

* Upgrade XBlock dependency and remove web-fragments dependency in favor of
  XBlock's packaging of this module.

0.16.0 - 2026-04-21
**********************************************

Fixed
=====

* Fix video block editor issues while editing in the Content Library

0.16.0 - 2026-04-21
**********************************************

Fixed
=====

* Removed XModuleMixin usage and related duplicated logic from all xblocks
* Renames xblocks_contrib/common → xblocks_contrib/legacy_utils

0.15.3 - 2026-04-02
**********************************************

Fixed
=====

* Removed XModuleMixin legacy attibs from Annotatable Block, Discussion XBlock, Html Block, Poll Block, Problem Block.
* Match video download link font size with transcripts

0.15.2 - 2026-03-30
**********************************************

Added
=====

* Removed XModuleMixin legacy attibs from wordcloud, video block, lti block

0.15.1 - 2026-03-18
**********************************************

Added
=====

* Implemented JSON-based view to fetch a PDF-block's settings.

0.15.0 - 2026-03-18
**********************************************

Added
=====

* Implemented the Discussion XBlock, extracted from edx-platform.

0.13.1 - 2026-03-09
**********************************************

Fixed
=====

* Fix TemplateDoesNotExist Error for capa templates.

0.13.0 - 2026-03-03
**********************************************

Added
=====

* Implemented the Video XBlock, extracted from edx-platform.


0.12.1 - 2026-03-03
**********************************************

Added
=====

* Adds Capa app entrypoints in setup.py.


0.12.0 - 2026-03-02
**********************************************

Added
=====

* Implemented the Problem XBlock, extracted from edx-platform.



0.11.1 - 2026-02-27
**********************************************

Fixed
=====

* Package data for PDF block (templates, static assets) was missing and is now included.

0.11.0 - 2026-01-26
**********************************************

Added
=====

* Implemented PDF Block, extracted from third party plugin.

0.6.0 – 2025-08-13
**********************************************

Added
=====

* Restore get_html in the extracted Annotatable XBlock to match existing edx-platform

0.5.0 – 2025-08-8
**********************************************

Added
=====

* Implemented the poll XBlock & HTML XBlock, extracted from edx-platform.

0.4.0 – 2025-05-7
**********************************************

Added
=====

* Implemented the LTI XBlock, extracted from edx-platform.


0.3.0 – 2025-04-8
**********************************************

Added
=====

* Added support for django 5.2.
* Implemented the Annotatable XBlock, extracted from edx-platform.


0.2.0 – 2025-02-12
**********************************************

Added
=====

* Implemented the Word Cloud Block, extracted from edx-platform.


0.1.0 – 2024-07-04
**********************************************

Added
=====

* First release on PyPI.
