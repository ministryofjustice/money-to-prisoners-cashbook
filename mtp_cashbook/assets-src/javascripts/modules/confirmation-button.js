// Confirmation button module
/* globals exports, $ */

'use strict';

exports.ConfirmationButton = {

  init: function () {
    $('.mtp-confirm__button').hide();

    $(document).on('change', '.Checkbox', function() {
      $('.mtp-confirm__button').toggle();
    });

    $(document).on('change', '.Checkbox', function() {
      this.$items = $('.js-RunningTotal-item').length;
      this.$completeItems = $('.js-RunningTotal-item:checked').length;

      if (this.$items === this.$completeItems) {
        $('#control-total, #entered-total').addClass('green');
      } else {
        $('#control-total, #entered-total').removeClass('green');
      };
    })
  }
};