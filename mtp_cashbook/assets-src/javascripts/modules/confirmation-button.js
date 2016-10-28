// Confirmation button module
/* globals exports, $ */

'use strict';

exports.ConfirmationButton = {

  init: function () {
    $('.mtp-confirm__button').hide();

    $(document).on('change', '.Checkbox', function() {
      $('.mtp-confirm__button').toggle();
    });

    $(document).on('change', '.Checkbox--left', function() {
      $('#control-total, #entered-total').toggleClass('green');
    })
  }
};