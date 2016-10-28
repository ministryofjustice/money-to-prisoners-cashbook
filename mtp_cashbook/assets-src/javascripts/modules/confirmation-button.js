// Confirmation button module
/* globals exports, $ */

'use strict';

exports.ConfirmationButton = {

  init: function () {
    $('.mtp-confirm__button').hide();

    $(document).on('change', '.Checkbox', function() {
      this.$items = $('.js-RunningTotal-item').length;
      this.$completeItems = $('.js-RunningTotal-item:checked').length;

      if (this.$completeItems > 0) {
        $('.mtp-confirm__button').show();
      } else {
        $('.mtp-confirm__button').hide();
      };

      if (this.$items === this.$completeItems) {
        $('#control-total, #entered-total').addClass('green');
      } else {
        $('#control-total, #entered-total').removeClass('green');
      };
    })
  }
};