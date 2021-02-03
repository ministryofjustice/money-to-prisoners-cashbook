'use strict';

import {BatchValidation} from './batch-validation';
import {SelectAll} from './select-all';
import {StickyHeader} from './sticky-header';

export var Cashbook = {
  init: function () {
    SelectAll.init();
    StickyHeader.init();
    BatchValidation.init();
    this.initSelectionCount();
    this.initConfirmManual();
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
  },

  initConfirmManual: function () {
    // display a dialogue box to ask for confirmation before submitting manual credit form
    $('.mtp-form--confirm-manual').on('click', ':submit', function (e) {
      var $el = $(e.target);
      var type = $el.val();

      if (type !== 'submit') {
        // 'Yes' was click in the confirmation dialogue box, so just actually submit
        return;
      }

      e.preventDefault();

      var creditID = $el.data('credit-id');
      $('#manual-confirm-dialogue-' + creditID).trigger('dialogue:open');
    });
  }
};