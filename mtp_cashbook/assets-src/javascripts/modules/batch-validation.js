// Batch validation module
/* global exports, require, analytics, $ */
'use strict';

var bindAll = require('lodash/function/bindAll');
var analytics = require('analytics');

exports.BatchValidation = {
  selector: '.js-BatchValidation',

  init: function () {
    bindAll(this, 'onSubmit');
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$form = $(this.selector);
    this.transactionsName = this.$form.data('transactions-name');
    this.$transactions = $('[name="' + this.transactionsName + '"]');
  },

  bindEvents: function () {
    this.base.Events.on('BatchValidation.render', this.render);
    this.$form.on('click', ':submit', this.onSubmit);
  },

  _allChecked: function () {
    var allChecked = true;

    this.$transactions.each(function (i, el) {
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

    this.$transactions.each(function (i, el) {
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

    if(type !== 'submit') {
      // If this is a 'Yes' click in the confirmation popup, so just
      // actually submit
      return;
    }

    // Check if this a total or a partial batch submission
    if (!checkedValid && numChecked > 0) {
      // Partial: ask for confirmation
      e.preventDefault();
      this.base.Events.trigger({
        type: 'Dialog.render',
        target: e.target,
        targetSelector: '#incomplete-batch-dialog'
      });
      analytics.analytics.send('pageview', '/batch/-dialog_open/');
      return;
    }
  }
};
