// Training section
/* globals exports */
'use strict';

exports.Training = {
  selector: '.mtp-training__print-link',

  init: function () {
    $(this.selector).click(function(e) {
      e.preventDefault();
      window.print();
    });
  }
};
