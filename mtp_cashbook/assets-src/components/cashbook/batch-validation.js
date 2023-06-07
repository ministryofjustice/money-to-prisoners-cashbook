// Batch validation module
'use strict';

import {Analytics} from 'mtp_common/components/analytics';

export var BatchValidation = {
  selector: '.mtp-form--batch-validation',

  init: function () {
    this.$form = $(this.selector);
    this.$credits = $('[name="' + this.$form.data('credits-name') + '"]');
    this.$form.on('click', ':submit', $.proxy(this.onSubmit, this));
  },

  _allChecked: function () {
    var allChecked = true;

    this.$credits.each(function (i, el) {
      var $item = $(el);

      if (!$item.is(':checked')) {
        allChecked = false;
        return false;
      }
    });

    return allChecked;
  },

  _numChecked: function () {
    var count = 0;

    this.$credits.each(function (i, el) {
      var $item = $(el);

      if ($item.is(':checked')) {
        count += 1;
      }
    });

    return count;
  },

  // display a dialogue box to ask for confirmation before submitting partial-selected credit list
  onSubmit: function (e) {
    var $el = $(e.target);
    var type = $el.val();
    var checkedValid = this._allChecked();
    var numChecked = this._numChecked();

    if (type !== 'submit') {
      // 'Yes' was click in the confirmation dialogue box, so just actually submit
      return;
    }

    // Check if this a total or a partial batch submission
    if (!checkedValid && numChecked > 0) {
      // Partial: ask for confirmation
      e.preventDefault();
      $('#incomplete-batch-dialogue').trigger('dialogue:open');
      var pageLocation = '/batch/-dialog_open/';
      Analytics.ga4SendPageView(pageLocation);
    }
  }
};
