// Align payment totals module
/* globals exports, $ */
'use strict';

exports.AlignTotals = {

  init: function () {
    this.cacheEls();
    if (this.ctrlTotal.length) {
      this.bindEvents();
    }
  },

  cacheEls: function () {
    this.$window = $(window);
    this.amount = $('td.numeric:first');
    this.ctrlTotal = $('.ctrl-total');
    this.entTotal = $('.entered-total');
  },

  bindEvents: function () {
    this.$window.load($.proxy(this.alignItems, this));
    this.$window.resize($.proxy(this.alignItems, this));
    this.$window.scroll($.proxy(this.alignItems, this));
  },

  alignItems: function () {
    var amountOffsetLeft = this.amount.offset().left;
    this.entTotal.offset({ left: amountOffsetLeft });
    this.ctrlTotal.offset({ left: amountOffsetLeft });
  }
};