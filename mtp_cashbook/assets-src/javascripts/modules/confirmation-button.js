// Confirmation button module
/* globals exports, $ */

'use strict';

exports.ConfirmationButton = {

  init: function () {
    $('.mtp-confirm__button').hide();

    $(".Checkbox").click(function(){
      $(".mtp-confirm__button").toggle();
    });
  }
};