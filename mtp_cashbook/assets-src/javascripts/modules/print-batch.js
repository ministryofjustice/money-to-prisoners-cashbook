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

    this.$iframe = $(
      '<iframe>', {'style': 'position: absolute; top: -1000px'}
    ).appendTo('body');

    this.$iframe.on('load', $.proxy(this.onLoadIframe, this));
    this.$iframe.attr('src', $(e.target).attr('href'));
  },

  onLoadIframe: function () {
    var printFrame = this.$iframe[0]

    printFrame.contentWindow.addEventListener(
      'afterprint', function () {printFrame.remove();}
    );

    try {
      if (!printFrame.contentWindow.document.execCommand('print', false, null)) {
        printFrame.contentWindow.print();
      }
    } catch (e) {
      printFrame.contentWindow.print();
    }
  }
};
