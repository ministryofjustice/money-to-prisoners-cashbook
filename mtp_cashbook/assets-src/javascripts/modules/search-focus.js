// Focus on search input field
'use strict';

exports.SearchFocus = {
  init: function () {
    var searchInputField = document.getElementById('id_search');
    if (searchInputField &&
        document.activeElement && document.activeElement.tagName === 'BODY' &&
        $('.error-summary').length === 0) {
      searchInputField.focus();
    }
  }
};
