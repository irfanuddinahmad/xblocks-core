/*
 * Test environment for the Annotatable XBlock JS specs.
 *
 * In the LMS, the jQuery qTip plugin is loaded globally and annotatable.js calls
 * `$(el).qtip(...)` on each highlighted span. The openedx-platform karma setup loaded the
 * real vendor plugin; here a no-op stub is enough for the constructor to run.
 */
(function($) {
    'use strict';

    if (!$.fn.qtip) {
        $.fn.qtip = function() {
            return this;
        };
    }

    jasmine.getFixtures().fixturesPath = 'base/fixtures';
}(jQuery));
