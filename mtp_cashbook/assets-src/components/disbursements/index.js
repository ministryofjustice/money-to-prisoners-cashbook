'use strict';

export var Disbursements = {
  init: function() {

    // update NOMIS balances without page reload
    $('.mtp-accounts-table tfoot a').click(function (e) {
      e.preventDefault();
      var $button = $(this);
      var $dataBoxes = $('.mtp-accounts-table__amount');
      var errorMessage = django.gettext('Please try again later');
      $dataBoxes.text(django.gettext('Please wait…'));
      $.ajax($button.attr('href')).done(function (response) {
        $dataBoxes.each(function () {
          var $dataBox = $(this);
          var data = response[$dataBox.data('balance')];
          $dataBox.text(data === undefined || data === null ? errorMessage : data);
        });
      }).fail(function () {
        $dataBoxes.text(errorMessage);
      });
    });

    // prevent new lines in wrapped textareas
    $('#id_remittance_description').keydown(function (e) {
      return e.keyCode !== 13;
    });

  }
};
