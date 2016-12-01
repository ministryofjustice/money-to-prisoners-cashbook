// Batch validation module
'use strict';

var analytics = require('analytics');

exports.BatchValidation = {
  selector: '.js-BatchValidation',

  init: function () {
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$form = $(this.selector);
    this.creditsName = this.$form.data('credits-name');
    this.$credits = $('[name="' + this.creditsName + '"]');
  },

  bindEvents: function () {
    this.$body.on('BatchValidation.render', this.render);
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

  // Called when the user submits the form,
  // either clicking 'Done' or 'Yes' in the popup.
  onSubmit: function (e) {
    var $el = $(e.target);
    var type = $el.val();
    var checkedValid = this._allChecked();
    var numChecked = this._numChecked();

    if (type !== 'submit') {
      // If this is a 'Yes' click in the confirmation popup, so just
      // actually submit
      return;
    }

    // Check if this a total or a partial batch submission
    if (!checkedValid && numChecked > 0) {
      // Partial: ask for confirmation
      e.preventDefault();
      this.$body.trigger({
        type: 'Dialog.render',
        target: e.target,
        targetSelector: '#incomplete-batch-dialog'
      });
      analytics.Analytics.send('pageview', '/batch/-dialog_open/');
      return;
    }
  }
};
