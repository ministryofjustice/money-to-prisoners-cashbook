'use strict';

exports.Disbursements = {
  init: function () {
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
