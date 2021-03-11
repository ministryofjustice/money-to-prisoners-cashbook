// Sticky header module
'use strict';

export var StickyHeader = {
  selector: '.mtp-sticky-header',
  stickyClass: 'mtp-sticky-header--sticky',

  init: function () {
    this.$originalHeader = $(this.selector);
    if (this.$originalHeader.length === 0) {
      return;
    }

    this.$window = $(window);
    this.$form = $('.mtp-form--batch-validation');
    this.$stickyHeader = this.$originalHeader.clone().addClass(this.stickyClass);
    this.offsetPosition = this.$originalHeader.offset().top + this.$originalHeader.height();

    $('body').on('StickyHeader.render', $.proxy(this.render, this));
    this.$window.scroll($.proxy(this.onScroll, this));
    this.render();
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
