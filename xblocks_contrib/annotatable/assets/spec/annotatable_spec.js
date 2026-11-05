/*
 * Ported from openedx-platform `xmodule/js/spec/annotatable/display_spec.js`
 * (removed by openedx/openedx-platform#38746, Slash-n-Burn epic openedx/openedx-platform#37819).
 * The fixture `fixtures/annotatable.html` is copied unchanged from `xmodule/js/fixtures/annotatable.html`.
 *
 * Only adaptation: the extracted block's initializer is the XBlock-style `Annotatable(runtime, element)`
 * instead of the built-in `new Annotatable(el)`.
 */
describe('Annotatable', function() {
    beforeEach(() => loadFixtures('annotatable.html'));
    describe('constructor', function() {
        const el = $('.xblock-student_view.xmodule_AnnotatableModule');
        beforeEach(function() {
            this.annotatable = new Annotatable({}, el);
        });
        it('works', () => expect(1).toBe(1));
    });
});
