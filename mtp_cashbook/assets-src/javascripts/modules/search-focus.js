// Focus on search input field
/* globals exports */
'use strict';

exports.SearchFocus = {
  init: function () {
    var searchInputField = document.getElementById('id_search');
    if (searchInputField && document.activeElement && document.activeElement.tagName === 'BODY') {
      searchInputField.focus();
    }
  }
};
