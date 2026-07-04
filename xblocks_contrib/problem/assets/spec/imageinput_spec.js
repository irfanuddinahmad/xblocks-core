/**
 * "Beware of bugs in the above code; I have only proved it correct, not tried
 * it."
 *
 * ~ Donald Knuth
 */

describe('ImageInput', function() {
  let state;

  beforeEach(function() {
    loadFixtures('imageinput.html');
    const $el = $('#imageinput_12345');
    $el.append(createTestImage('cross_12345', 300, 400, 'red'));
    state = new ImageInput('12345');
  });

  it('initialization', function() {
    expect(state.el).toBeDefined();
    expect(state.el).toExist();

    expect(state.crossEl).toBeDefined();
    expect(state.crossEl).toExist();

    expect(state.inputEl).toBeDefined();
    expect(state.inputEl).toExist();

    expect(state.el).toHandle('click');
  });

  it('cross becomes visible after first click', function() {
    expect(state.crossEl.css('visibility')).toBe('hidden');
    state.el.click();
    expect(state.crossEl.css('visibility')).toBe('visible');
  });

  it('coordinates are updated [offsetX is set]', function() {
    const event = jQuery.Event('click', { offsetX: 35.3, offsetY: 42.7 });
    const posX = event.offsetX;
    const posY = event.offsetY;

    jQuery(state.el).trigger(event);

    const cssLeft = stripPx(state.crossEl.css('left'));
    const cssTop = stripPx(state.crossEl.css('top'));

    expect(cssLeft).toBeCloseTo(posX - 15, 1);
    expect(cssTop).toBeCloseTo(posY - 15, 1);
    expect(state.inputEl.val()).toBe(`[${Math.round(posX)},${Math.round(posY)}]`);
  });

  it('coordinates are updated [offsetX is NOT set]', function() {
    const offset = state.el.offset();
    const event = jQuery.Event('click', {
      offsetX: undefined,
      offsetY: undefined,
      pageX: 35.3,
      pageY: 42.7,
    });
    const posX = event.pageX - offset.left;
    const posY = event.pageY - offset.top;

    jQuery(state.el).trigger(event);

    const cssLeft = stripPx(state.crossEl.css('left'));
    const cssTop = stripPx(state.crossEl.css('top'));

    expect(cssLeft).toBeCloseTo(posX - 15, 1);
    expect(cssTop).toBeCloseTo(posY - 15, 1);
    expect(state.inputEl.val()).toBe(`[${Math.round(posX)},${Math.round(posY)}]`);
  });

  // Generate a simple canvas-based image on the fly rather than loading a fixture file.
  function createTestImage(id, width, height, fillStyle) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    ctx.fillStyle = fillStyle;
    ctx.fillRect(0, 0, width, height);

    const img = document.createElement('img');
    img.src = canvas.toDataURL('image/png');
    img.id = id;

    return img;
  }

  // Strip the trailing 'px' from a CSS left/top value string.
  function stripPx(str) {
    return str.substring(0, str.length - 2);
  }
});
