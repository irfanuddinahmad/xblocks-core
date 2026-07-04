/**
 * Simple image input
 *
 * Click on image. Update the coordinates of a dot on the image.
 * The new coordinates are the location of the click.
 */
class ImageInput {
  constructor(elementId) {
    this.el = $(`#imageinput_${elementId}`);
    this.crossEl = $(`#cross_${elementId}`);
    this.inputEl = $(`#input_${elementId}`);
    this.el.on('click', this.clickHandler.bind(this));
  }

  clickHandler(event) {
    const offset = this.el.offset();
    // offsetX/Y is unavailable in some older browsers; fall back to pageX/Y minus element offset.
    const posX = event.offsetX !== undefined ? event.offsetX : event.pageX - offset.left;
    const posY = event.offsetY !== undefined ? event.offsetY : event.pageY - offset.top;
    // Round to reduce float differences across browsers (IE10 returns floats, Chrome/FF integers).
    const result = `[${Math.round(posX)},${Math.round(posY)}]`;

    this.crossEl.css({
      left: posX - 15,
      top: posY - 15,
      visibility: 'visible',
    });

    this.inputEl.val(result);
  }
}

window.ImageInput = ImageInput;
