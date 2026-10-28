// Submit once module
// Stops a form being submitted twice, whichever of its submit buttons is used: a double click, the copy of the button
// in the sticky header, or a confirmation dialogue button
'use strict';

export var SubmitOnce = {
  selector: '.mtp-form--submit-once',

  init: function () {
    // delegated, so this runs after handlers bound to the form itself and can see whether they cancelled the submission
    $(document).on('submit', this.selector, function (e) {
      var $form = $(this);

      if ($form.data('submitted')) {
        e.preventDefault();
        return;
      }
      if (e.isDefaultPrevented()) {
        return;
      }

      $form.data('submitted', true);
      // disable the buttons only once the browser has put the clicked button's name and value in the request;
      // the view uses them to tell which form was submitted
      setTimeout(function () {
        $form.find(':submit').prop('disabled', true).attr('aria-disabled', 'true');
      }, 0);
    });

    // a page restored from the back-forward cache keeps its state, so allow the form to be used again
    $(window).on('pageshow', function (e) {
      if (e.originalEvent && e.originalEvent.persisted) {
        $(SubmitOnce.selector).each(function () {
          $(this).removeData('submitted').find(':submit').prop('disabled', false).removeAttr('aria-disabled');
        });
      }
    });
  }
};
