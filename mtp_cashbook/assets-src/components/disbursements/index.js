'use strict';

export var Disbursements = {
  init: function() {
    // prevent new lines in wrapped textareas
    $('#id_remittance_description').keydown(function (e) {
      return e.keyCode !== 13;
    });
  }
};
