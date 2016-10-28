// Confirmation button module
/* globals exports, $ */

'use strict';

exports.ConfirmationButton = {

  init: function () {
    $('.mtp-confirm__button').hide();

    $(document).on('change', '.Checkbox', function() {
      var items = $('.js-RunningTotal-item').length;
      var completeItems = $('.js-RunningTotal-item:checked').length;

      if (completeItems > 0) {
        $('.mtp-confirm__button').show();
      } else {
        $('.mtp-confirm__button').hide();
      };

      if (items === completeItems) {
        $('#control-total, #entered-total').addClass('green');
      } else {
        $('#control-total, #entered-total').removeClass('green');
      };
    })
  }
};