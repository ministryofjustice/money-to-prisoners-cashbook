'use strict';

import {SelectAll} from './select-all';

export var Cashbook = {
  init: function () {
    SelectAll.init();
    this.initSelectionCount();
  },

  initSelectionCount: function () {
    // displays a running count of selected credits
    $('.mtp-input--selection-count').each(function () {
      var $countContainer = $(this);
      $('.mtp-input--counted').on('change', function () {
        var itemCount = $('.mtp-input--counted:checked').length;
        if (itemCount > 0) {
          var message = django.ngettext(
            '%(count)s credit selected for processing in NOMIS.',
            '%(count)s credits selected for processing in NOMIS.',
            itemCount
          );
          $countContainer.html(
            django.interpolate(message, {'count': '<strong>' + itemCount + '</strong>'}, true)
          );
        } else {
          $countContainer.text(
            django.gettext('You haven’t selected any to process yet.')
          );
        }
      });
    });
  }
};
