const Collapsible = {
  setCollapsibles,
  toggleFull,
  toggleHint,
};

function setCollapsibles(el) {
  const linkTop = '<a href="#" class="full full-top">See full output</a>';
  const linkBottom = '<a href="#" class="full full-bottom">See full output</a>';

  // Standard longform + shortfom pattern.
  el.find(".longform").hide();
  el.find(".shortform").append(linkTop, linkBottom); // xss-lint: disable=javascript-jquery-append

  // Custom longform + shortform text pattern.
  const short_custom = el.find(".shortform-custom");

  // Set up each one individually.
  short_custom.each(function (index, elt) {
    const open_text = $(elt).data("open-text");
    const close_text = $(elt).data("close-text");
    edx.HtmlUtils.append(
      $(elt),
      edx.HtmlUtils.joinHtml(
        edx.HtmlUtils.HTML("<a href='#' class='full-custom'>"),
        gettext(open_text),
        edx.HtmlUtils.HTML("</a>"),
      ),
    );

    $(elt)
      .find(".full-custom")
      .click(function (event) {
        Collapsible.toggleFull(event, open_text, close_text);
      });
  });

  // Collapsible pattern.
  el.find(".collapsible header + section").hide();

  // Set up triggers.
  el.find(".full").click(function (event) {
    Collapsible.toggleFull(event, "See full output", "Hide output");
  });
  el.find(".collapsible header a").click(Collapsible.toggleHint);
}

function toggleFull(event, open_text, close_text) {
  event.preventDefault();

  const parent = $(event.target).parent();
  parent.siblings().slideToggle();
  parent.parent().toggleClass("open");

  const new_text = $(event.target).text() === open_text ? close_text : open_text;

  let $el;
  if ($(event.target).hasClass("full")) {
    $el = parent.find(".full");
  } else {
    $el = $(event.target);
  }

  $el.text(new_text);
}

function toggleHint(event) {
  event.preventDefault();

  $(event.target).parent().siblings().slideToggle();
  $(event.target).parent().parent().toggleClass("open");
}

window.Collapsible = Collapsible;
