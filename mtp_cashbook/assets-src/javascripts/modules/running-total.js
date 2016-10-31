// Running Total module
/* globals exports, $ */
'use strict';

exports.RunningTotal = {
  selector: '.js-RunningTotal',

  init: function () {
    this.cacheEls();

    if (this.$totalsContainer.length) {
      this.bindEvents();
      this.render();
    }
  },

  cacheEls: function () {
    this.$body = $('body');
    this.$items = $('.js-RunningTotal-item');
    this.$totalsContainer = $(this.selector);
    this.labelText = this.$totalsContainer.data('label');

    this.$label = $('<p>').addClass('label print-hidden');
    this.$total = $('<span>').addClass('total js-RunningTotal-total');
  },

  bindEvents: function () {
    this.$body.on('RunningTotal.render', $.proxy(this.render, this));
    this.$items.on('change', $.proxy(this.updateTotal, this));
  },

  updateTotal: function () {
    var total = this.calculateTotal();

    $('.js-RunningTotal-total').html('&pound;' + total);
    this.$noItems = $('.js-RunningTotal-item:checked').length;
    $('.count-checked-checkboxes').html(this.$noItems);
  },

  calculateTotal: function () {
    var total = 0;

    this.$items.each(function (i, el) {
      var $el = $(el);
      var amount = $el.data('amount');

      if ($el.is(':checked')) {
        total += parseFloat(amount);
      }
    });

    return total.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
  },

  render: function () {
    this.$label
      .attr('aria-live', 'polite')
      .attr('aria-atomic', 'false')
      .html('<span class="label">' + this.labelText + '</span>')
      .append(this.$total);

    this.$totalsContainer
      .append(this.$label);

    this.updateTotal();
  }
};
