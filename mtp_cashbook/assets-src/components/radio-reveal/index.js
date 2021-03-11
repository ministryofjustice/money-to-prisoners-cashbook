// Conditionally revealed targets linked to radio buttons
'use strict';

export var RadioReveal = {
  init: function () {
    var $inputs = $('.mtp-radio-reveal');
    var revealSets = {};

    function changed (e) {
      var name = e.target.name;
      var revealSet = revealSets[name];
      for (var i in revealSet) {
        if (Object.prototype.hasOwnProperty.call(revealSet, i)) {
          var group = revealSet[i];
          if (group.$input.prop('checked')) {
            group.$target.removeClass('mtp-!-display-none-js-enabled-only govuk-!-display-none');
          } else {
            group.$target.addClass('mtp-!-display-none-js-enabled-only');
          }
        }
      }
    }

    $inputs.each(function () {
      var $input = $(this);
      var name = $input.attr('name');
      var $target = $($input.data('reveal'));

      revealSets[name] = revealSets[name] || [];
      revealSets[name].push({
        $input: $input,
        $target: $target
      });
      $input.click(changed);
      if ($input.is(':checked')) {
        $input.click();
      }
    });
  }
};
