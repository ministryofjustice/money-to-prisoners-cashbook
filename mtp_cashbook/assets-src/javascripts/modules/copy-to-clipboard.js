/* globals exports, $ */
'use strict';

exports.CopyToClipboard = {
  init: function () {
    $('.copy-to-clipboard').on('click', function() {
      var copyText = $(this).prev('span').text();
      var holdText = document.getElementById('holdText');
      holdText.innerText = copyText;
      var copied = holdText.createTextRange();
      copied.execCommand('copy');
    });
  }
};
