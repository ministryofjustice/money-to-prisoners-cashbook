// Prints the target of a link using an iframe
/* globals Sentry */
'use strict';

export var PrintLinkTarget = {
  linkSelector: '.mtp-print-link-target',

  init: function () {
    $('body').on('click', this.linkSelector, $.proxy(this.onClickPrint, this));
  },

  onClickPrint: function (e) {
    e.preventDefault();

    this.$iframe = $(
      '<iframe>', {'style': 'position: absolute; top: -1000px'}
    ).appendTo('body');
    this.$iframe.on('load', $.proxy(this.onLoadIframe, this));
    this.$iframe.attr('src', $(e.target).attr('href'));
  },

  onLoadIframe: function () {
    var printFrame = this.$iframe[0];

    $(printFrame.contentWindow).on('afterprint', function () {
      printFrame.remove();
    });

    try {
      printFrame.contentWindow.print();
    } catch (error) {
      if (Sentry !== undefined) {
        Sentry.captureException(error);
      }
    }
  }
};
