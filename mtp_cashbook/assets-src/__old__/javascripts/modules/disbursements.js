'use strict';

exports.Disbursements = {
  init: function () {
    // show note explaining why current user cannot confirm a payment
    $('.mtp-confirm-disbursements-list .mtp-question-button').click(function (e) {
      e.preventDefault();
      var $button = $(this);
      var $row = $button.parents('tr');
      var $infoRow = $row.next();
      if ($row.hasClass('mtp-pending-cannot-confirm-row')) {
        $row.removeClass('mtp-pending-cannot-confirm-row');
        $infoRow.addClass('mtp-!-display-none-js-enabled-only');
      } else {
        $row.addClass('mtp-pending-cannot-confirm-row');
        $infoRow.removeClass('mtp-!-display-none-js-enabled-only');
      }
    });
  }
};
