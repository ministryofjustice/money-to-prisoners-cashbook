// Running Total module
'use strict';

exports.SelectionCount = {
  selector: '.js-SelectionCount',

  init: function () {
    this.cacheEls();

    if (this.$countContainer.length) {
      this.bindEvents();
      this.render();
    }
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$items = $('.js-SelectionCount-item');
    this.$countContainer = $(this.selector);
  },

  bindEvents: function () {
    this.$body.on('SelectionCount.render', $.proxy(this.render, this));
    this.$items.on('change', $.proxy(this.updateCount, this));
  },

  updateCount: function () {
    this.$itemCount = $('.js-SelectionCount-item:checked').length;
    this.$countContainer.html(this.$itemCount);

    if (this.$itemCount > 0) {
      $('.mtp-none-selected').hide();
      $('.mtp-some-selected').show();
    } else {
      $('.mtp-none-selected').show();
      $('.mtp-some-selected').hide();
    }
  },

  render: function () {
    this.updateCount();
  }
};
