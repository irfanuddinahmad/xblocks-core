describe("Collapsible", function () {
  let $el;
  const initialize = function (template) {
    setFixtures(template);
    $el = $(".collapsible");
    Collapsible.setCollapsibles($el);
  };
  const disableFx = function () {
    $.fx.off = true;
  };
  const enableFx = function () {
    $.fx.off = false;
  };

  let html, html_custom;
  beforeEach(function () {
    html =
      "" +
      '<section class="collapsible">' +
      '<div class="shortform">shortform message</div>' +
      '<div class="longform">' +
      "<p>longform is visible</p>" +
      "</div>" +
      "</section>";
    html_custom =
      "" +
      '<section class="collapsible">' +
      "<div " +
      'class="shortform-custom" ' +
      'data-open-text="Show shortform-custom" ' +
      'data-close-text="Hide shortform-custom"' +
      ">shortform message</div>" +
      '<div class="longform">' +
      "<p>longform is visible</p>" +
      "</div>" +
      "</section>";
  });

  describe("setCollapsibles", function () {
    it("Default container initialized correctly", function () {
      initialize(html);

      expect($el.find(".shortform")).toContainElement(".full-top");
      expect($el.find(".shortform")).toContainElement(".full-bottom");
      expect($el.find(".longform")).toBeHidden();
      expect($el.find(".full")).toHandle("click");
    });

    it("Custom container initialized correctly", function () {
      initialize(html_custom);

      expect($el.find(".shortform-custom")).toContainElement(".full-custom");
      expect($el.find(".full-custom")).toHaveText("Show shortform-custom");
      expect($el.find(".longform")).toBeHidden();
      expect($el.find(".full-custom")).toHandle("click");
    });
  });

  describe("toggleFull", function () {
    const assertChanges = function (state, anchorsElClass, showText, hideText) {
      if (state == null) {
        state = "closed";
      }

      const anchors = $el.find("." + anchorsElClass);

      let text;
      if (state === "closed") {
        expect($el.find(".longform")).toBeHidden();
        expect($el).not.toHaveClass("open");
        text = showText;
      } else {
        expect($el.find(".longform")).toBeVisible();
        expect($el).toHaveClass("open");
        text = hideText;
      }

      $.each(anchors, function (index, el) {
        expect(el).toHaveText(text);
      });
    };

    beforeEach(function () {
      disableFx();
    });

    afterEach(function () {
      enableFx();
    });

    it("Default container", function () {
      initialize(html);

      const event = jQuery.Event("click", {
        target: $el.find(".full").get(0),
      });

      Collapsible.toggleFull(event, "See full output", "Hide output");
      assertChanges("opened", "full", "See full output", "Hide output");

      Collapsible.toggleFull(event, "See full output", "Hide output");
      assertChanges("closed", "full", "See full output", "Hide output");
    });

    it("Custom container", function () {
      initialize(html_custom);

      const event = jQuery.Event("click", {
        target: $el.find(".full-custom").get(0),
      });

      Collapsible.toggleFull(event, "Show shortform-custom", "Hide shortform-custom");
      assertChanges("opened", "full-custom", "Show shortform-custom", "Hide shortform-custom");

      Collapsible.toggleFull(event, "Show shortform-custom", "Hide shortform-custom");
      assertChanges("closed", "full-custom", "Show shortform-custom", "Hide shortform-custom");
    });
  });
});
