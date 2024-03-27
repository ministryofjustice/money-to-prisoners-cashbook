'use strict';

export var Disbursements = {
  init: function () {
    this.initAmount();
    this.initRecipientAddress();
    this.initRecipientBankAccount();
    this.initRemittanceDescription();
    this.initPendingList();
  },

  initAmount: function () {
    // update NOMIS balances without page reload
    $('.mtp-accounts-table tfoot a').click(function (e) {
      e.preventDefault();

      if(typeof django === 'undefined') {
        // if django js library hasn't loaded yet, fall back to no translation
        window.django = {
          gettext: function(text) {
            return text;
          }
        };
      }

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
  },

  initRecipientAddress: function () {
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
  },

  initRecipientBankAccount: function () {
    // as-you-type formatting of sort codes
    $('.mtp-input--sort-code').each(function () {
      var $control = $(this);
      var sortCodeCleaner = /[^0-9-]+/;
      var sortCodeMatcher = /^(\d\d)(-?((\d\d)(-?(\d\d)?)?)?)?$/;

      function update () {
        var value = $control.val().replace(sortCodeCleaner, '');
        var match = sortCodeMatcher.exec(value);
        if (match) {
          var newValue = '';
          if (match[1]) {
            newValue += match[1];
          }
          if (match[4]) {
            newValue += '-' + match[4];
          }
          if (match[6]) {
            newValue += '-' + match[6];
          }
          if (newValue) {
            $control.val(newValue);
          }
        }
      }

      $control.keyup(update);
      update();
    });
  },

  initRemittanceDescription: function () {
    // prevent new lines in wrapped textareas
    $('#id_remittance_description').keydown(function (e) {
      return e.key !== 'Enter';
    });
  },

  initPendingList: function () {
    // show note explaining why current user cannot confirm a payment
    $('.mtp-table--pending-list__question-button').click(function (e) {
      e.preventDefault();
      var $button = $(this);
      var $row = $button.parents('tr');
      var $infoRow = $row.next();
      if ($row.hasClass('mtp-table--pending-list__question-row')) {
        $row.removeClass('mtp-table--pending-list__question-row');
        $infoRow.addClass('mtp-!-display-none-js-enabled-only');
      } else {
        $row.addClass('mtp-table--pending-list__question-row');
        $infoRow.removeClass('mtp-!-display-none-js-enabled-only');
      }
    });
  }
};
