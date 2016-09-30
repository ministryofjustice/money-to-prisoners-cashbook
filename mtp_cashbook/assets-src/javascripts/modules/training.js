// Training section
/* globals exports */
'use strict';

exports.Training = {
  selector: '.mtp-training-navigation__js-print',

  init: function () {
    $(this.selector).click(function(e) {
      e.preventDefault();
      window.print();
    });
  }
};
