'use strict';

exports.Disbursements = {
  init: function () {
    // update NOMIS balances without page reload
    $('.mtp-refresh-row a').click(function (e) {
      e.preventDefault();
      var $button = $(this);
      var $dataBoxes = $('.mtp-balance-column');
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

    // show note explaining why current user cannot confirm a payment
    $('.mtp-confirm-disbursements-list .mtp-question-button').click(function (e) {
      e.preventDefault();
      var $button = $(this);
      var $row = $button.parents('tr');
      var $infoRow = $row.next();
      if ($row.hasClass('mtp-pending-cannot-confirm-row')) {
        $row.removeClass('mtp-pending-cannot-confirm-row');
        $infoRow.addClass('js-hidden');
      } else {
        $row.addClass('mtp-pending-cannot-confirm-row');
        $infoRow.removeClass('js-hidden');
      }
    });
  }
};
