// Training section
/* globals exports */
'use strict';

exports.Training = {
  selector: '.training-navigation--print',

  init: function () {
    $(this.selector).click(function(e) {
      e.preventDefault();
      window.print();
    });
  }
};
