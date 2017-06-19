// Print module
'use strict';

exports.PrintBatch = {
  linkSelector: '.js-PrintBatch',

  init: function () {
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
    this.$body = $('body');
  },

  bindEvents: function () {
    this.$body.on('click', this.linkSelector, $.proxy(this.onClickPrint, this));
  },

  onClickPrint: function (e) {
    e.preventDefault();

    this.$iframe = $('<iframe>', {'style': 'visibility: hidden'}).appendTo('body');

    this.$iframe.on('load', $.proxy(this.onLoadIframe, this));
    this.$iframe.attr('src', $(e.target).attr('href'));
  },

  onLoadIframe: function (e) {
    try {
      this.$iframe[0].contentWindow.document.execCommand('print', false, null);
    } catch (e) {
      this.$iframe[0].contentWindow.print();
    } finally {
      this.$iframe.remove()
    }
  }
};
