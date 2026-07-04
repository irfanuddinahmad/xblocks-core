/**
 * Set of library functions that provide common interface for javascript loading
 * for all module types. All functionality provided by JavascriptLoader should take
 * place at module scope, i.e. don't run jQuery over entire page.
 *
 * executeModuleScripts:
 *     Scan the module ('el') for "script_placeholder"s, then:
 *
 *     1) Fetch each script from server
 *     2) Explicitly attach the script to the <head> of document
 *     3) Explicitly wait for each script to be loaded
 *     4) Return to callback function when all scripts loaded
 */
function JavascriptLoader() {}

JavascriptLoader.executeModuleScripts = function (el, callback) {
  if (!callback) {
    callback = null; // eslint-disable-line no-param-reassign
  }
  const placeholders = el.find(".script_placeholder");
  if (placeholders.length === 0) {
    if (callback !== null) {
      callback();
    }
    return [];
  }
  // TODO: Verify the execution order of multiple placeholders
  const completed = (function () {
    const results = [];
    for (let i = 1, ref = placeholders.length; ref >= 1 ? i <= ref : i >= ref; ref >= 1 ? ++i : --i) {
      results.push(false);
    }
    return results;
  })();
  let callbackCalled = false;
  const completionHandlerGenerator = function (index) {
    return function () {
      let allComplete = true;
      completed[index] = true;
      for (let i = 0, len = completed.length; i < len; i++) {
        if (!completed[i]) {
          allComplete = false;
          break;
        }
      }
      if (allComplete && !callbackCalled) {
        callbackCalled = true;
        if (callback !== null) {
          return callback();
        }
      }
      return undefined;
    };
  };
  // Keep a map of what sources we're loaded from, and don't do it twice.
  const loaded = {};
  return placeholders.each(function (index, placeholder) {
    // TODO: Check if the script already exists in DOM. If so, (1) copy it
    // into memory; (2) delete the DOM script element; (3) reappend it.
    // This would prevent memory bloat and save a network request.
    const src = $(placeholder).attr("data-src");
    if (/^\s*(javascript|data|vbscript):/i.test(src)) {
      console.warn("Blocked unsafe script source:", src);
      completionHandlerGenerator(index)();
      return $(placeholder).remove();
    }
    const src_escaped = String(src || "")
      .replace(/</g, "%3C")
      .replace(/>/g, "%3E");
    if (!(src_escaped in loaded)) {
      loaded[src_escaped] = true;
      const s = document.createElement("script");
      s.setAttribute("src", src_escaped);
      s.setAttribute("type", "text/javascript");
      s.onload = completionHandlerGenerator(index);
      // Need to use the DOM elements directly or the scripts won't execute properly.
      $("head")[0].appendChild(s);
    } else {
      // just call the completion callback directly, without reloading the file
      completionHandlerGenerator(index)();
    }
    return $(placeholder).remove();
  });
};

window.JavascriptLoader = JavascriptLoader;
