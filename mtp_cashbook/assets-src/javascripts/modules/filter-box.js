// Disclosing box containing filters
'use strict';

exports.FilterBox = {
  init: function () {
    $('.mtp-filter-box__control').each(function () {
      var $controlContainer = $(this);
      var $button = $controlContainer.find('a');
      var $contents = $('#' + $button.attr('aria-controls'));
      var currentlyExpanded = $button.attr('aria-expanded') !== 'true';

      $button.click(function (e) {
        e.preventDefault();
        if (currentlyExpanded) {
          $contents.hide();
          $button.attr('aria-expanded', 'false');
          $controlContainer.removeClass('mtp-filter-box__control--expanded');
        } else {
          $contents.show();
          $button.attr('aria-expanded', 'true');
          $controlContainer.addClass('mtp-filter-box__control--expanded');
        }
        currentlyExpanded = !currentlyExpanded;
        return false;
      });
      $button.click();
    });
  }
};
