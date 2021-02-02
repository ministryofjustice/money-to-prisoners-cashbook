'use strict';

export var Disbursements = {
  init: function () {

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

    // fills recipient address form from select field
    $('.mtp-select__address').each(function () {
      var $addressSelect = $(this);

      var $addressLine1 = $('#id_address_line1');
      var $addressLine2 = $('#id_address_line2');
      var $city = $('#id_city');
      var $postcode = $('#id_postcode');

      $addressSelect.change(function () {
        if ($addressSelect.val()) {
          var $selectedAddress = $('option:selected', $addressSelect);
          var addressData = $selectedAddress.data('address');
          $addressLine1.val(addressData['address_line1']);
          $addressLine2.val(addressData['address_line2']);
          $city.val(addressData['city']);
          $postcode.val(addressData['postcode']);
        }
      });
    });

    // prevent new lines in wrapped textareas
    $('#id_remittance_description').keydown(function (e) {
      return e.keyCode !== 13;
    });

  }
};
