// Sticky header module
'use strict';

exports.StickyHeader = {
  selector: '.js-StickyHeader',

  stickyClass: 'is-sticky',

  init: function () {
    this.cacheEls();
    if (this.$originalHeader.length) {
      this.bindEvents();
      this.render();
    }
  },

  cacheEls: function () {
    this.$originalHeader = $(this.selector);

    if (this.$originalHeader.length) {
      this.$window = $(window);
      this.$body = $('body');
      this.$form = $('form.js-BatchValidation');
      this.$stickyHeader = this.$originalHeader.clone().addClass(this.stickyClass);
      this.offsetPosition = this.$originalHeader.offset().top + this.$originalHeader.height();
    }
  },

  bindEvents: function () {
    this.$body.on('StickyHeader.render', $.proxy(this.render, this));
    this.$window.scroll($.proxy(this.onScroll, this));
  },

  onScroll: function () {
    if (this.$window.scrollTop() >= this.offsetPosition) {
      if (!this.$stickyHeader.is(':visible')) {
        this.$stickyHeader
          .css({
            top: -this.$originalHeader.height()
          })
          .show()
          .stop()
          .animate({
            top: 0
          }, 500);
      }
    } else {
      this.$stickyHeader
        .stop()
        .animate({
          top: -this.$originalHeader.height()
        }, 150, 'linear', function () {
          $(this).hide();
        });
    }
  },

  render: function () {
    this.$stickyHeader.hide();
    this.$form.append(this.$stickyHeader);
  }
};
