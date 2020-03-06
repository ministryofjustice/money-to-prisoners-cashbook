// Conditionally revealed targets linked to radio buttons
'use strict';

exports.ConditionallyRevealed = {
  init: function () {
    var $inputs = $('.mtp-radio-reveal');
    var revealSets = {};

    function changed (e) {
      var name = e.target.name;
      var revealSet = revealSets[name];
      for (var i in revealSet) {
        if (revealSet.hasOwnProperty(i)) {
          var group = revealSet[i];
          if (group.$input.prop('checked')) {
            group.$target.removeClass('js-hidden hidden');
          } else {
            group.$target.addClass('js-hidden');
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
