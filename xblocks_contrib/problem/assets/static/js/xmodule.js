const XModule = {};

XModule.Descriptor = (function () {
  /*
   * Bind the module to an element. This may be called multiple times,
   * if the element content has changed and so the module needs to be rebound
   *
   * @method: constructor
   * @param {html element} the .xmodule_edit section containing all of the descriptor content
   */
  const Descriptor = function (element) {
    this.element = element;
    this.update = _.bind(this.update, this);
  };

  /*
   * Register a callback method to be called when the state of this
   * descriptor is updated. The callback will be passed the results
   * of calling the save method on this descriptor.
   */
  Descriptor.prototype.onUpdate = function (callback) {
    if (!this.callbacks) {
      this.callbacks = [];
    }

    this.callbacks.push(callback);
  };

  /*
   * Notify registered callbacks that the state of this descriptor has changed
   */
  Descriptor.prototype.update = function () {
    const data = this.save();
    const callbacks = this.callbacks;

    $.each(callbacks, function (index, callback) {
      callback(data);
    });
  };

  /*
   * Return the current state of the descriptor (to be written to the module store)
   *
   * @method: save
   * @returns {object} An object containing children and data attributes (both optional).
   *                   The contents of the attributes will be saved to the server
   */
  Descriptor.prototype.save = function () {
    return {};
  };

  return Descriptor;
}());

const XBlockToXModuleShim = function (runtime, element, initArgs) {
  /*
   * Load a single module (either an edit module or a display module)
   * from the supplied element, which should have a data-type attribute
   * specifying the class to load
   */
  let moduleType;

  if (initArgs) {
    moduleType = initArgs['xmodule-type'];
  }
  if (!moduleType) {
    moduleType = $(element).data('type');
  }

  if (moduleType === 'None') {
    return;
  }

  try {
    const module = new window[moduleType](element, runtime);

    if ($(element).hasClass('xmodule_edit')) {
      $(document).trigger('XModule.loaded.edit', [element, module]);
    }

    if ($(element).hasClass('xmodule_display')) {
      $(document).trigger('XModule.loaded.display', [element, module]);
    }

    return module;
  } catch (error) {
    console.error(`Unable to load ${moduleType}: ${error.message}`);
  }
};

window.XModule = XModule;
window.XBlockToXModuleShim = XBlockToXModuleShim;
