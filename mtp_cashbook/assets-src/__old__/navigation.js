// Non-desktop navigation interaction
'use strict';

exports.Navigation = {
  init: function () {
    $('.mtp-nav-search__trigger a').click(function () {
      $('.mtp-nav-search').addClass('mtp-nav-search--open');
      $(this).parent().remove();
      $('#id_search').focus();
    });
  }
};
