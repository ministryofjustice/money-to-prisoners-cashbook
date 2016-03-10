/* globals exports, $ */
'use strict';

exports.CopyToClipboard = {
  init: function () {
    $('.copy-to-clipboard').on('mouseover', function() {
      var bubble = $(this).next('span');
      bubble.removeClass('copied').text('Copy prisoner number to clipboard').show();
    });

    $('.copy-to-clipboard').on('mouseout', function() {
      var bubble = $(this).next('span');
      bubble.hide();
    });

    $('.copy-to-clipboard').on('click', function() {
      var bubble = $(this).next('span');
      var copyText = $(this).prev('span').text();
      if (document.body.createTextRange) {
        var holdText = document.getElementById('holdText');
        holdText.innerText = copyText;
        var copied = holdText.createTextRange();
        copied.execCommand('copy');
      } else {
        var textField = document.createElement('textarea');
        textField.innerText = copyText;
        document.body.appendChild(textField);
        textField.select();
        document.execCommand('copy');
        $(textField).remove();
      }
      bubble.addClass('copied').text('Copied!').show();
      setTimeout(function() { bubble.hide(); }, 500);
    });
  }
};
