// As-you-type formatting of sort codes
'use strict';

exports.SortCode = {
  init: function () {
    $('.mtp-sort-code-control').each(function () {
      var $control = $(this);
      var sortCodeCleaner = /[^0-9-]+/;
      var sortCodeMatcher = /^(\d\d)(-?((\d\d)(-?(\d\d)?)?)?)?$/;
      $control.keyup(function () {
        var value = $control.val().replace(sortCodeCleaner, '');
        var match = sortCodeMatcher.exec(value);
        if (match) {
          var newValue = '';
          if (match[1]) {
            newValue += match[1];
          }
          if (match[4]) {
            newValue += '-' + match[4];
          }
          if (match[6]) {
            newValue += '-' + match[6];
          }
          if (newValue) {
            $control.val(newValue);
          }
        }
      });
    });
  }
};
