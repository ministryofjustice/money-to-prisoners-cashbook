// Address picker module
'use strict';

exports.AddressPicker = {
  init: function () {
    this.bindAddressSelection();
  },

  bindAddressSelection: function () {
    var addressSelect = $('#address-select');

    var addressLine1 = $('#id_address_line1');
    var addressLine2 = $('#id_address_line2');
    var city = $('#id_city');
    var postcode = $('#id_postcode');

    function update () {
      if (addressSelect.val()) {
        var selectedAddress = $('#address-select option:selected');
        var addressData = selectedAddress.data('address');
        addressLine1.val(addressData.address_line1);
        addressLine2.val(addressData.address_line2);
        city.val(addressData.city);
        postcode.val(addressData.postcode);
      }
    }

    addressSelect.change(update);
  }
};
