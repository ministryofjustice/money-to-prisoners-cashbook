// Running Total module
'use strict';

exports.SelectionCount = {
  init: function () {
    this.$countContainer = $('.js-SelectionCount');
    if (this.$countContainer.length) {
      this.$items = $('.js-SelectionCount-item');
      this.$items.on('change', $.proxy(this.updateCount, this));
      this.updateCount();
    }
  },

  updateCount: function () {
    var itemCount = $('.js-SelectionCount-item:checked').length;
    if (itemCount > 0) {
      var message = django.ngettext(
        '%(count)s credit selected for processing in NOMIS.',
        '%(count)s credits selected for processing in NOMIS.',
        itemCount
      );
      this.$countContainer.html(
        django.interpolate(message, {'count': '<strong>' + itemCount + '</strong>'}, true)
      );
    } else {
      this.$countContainer.text(
        django.gettext('You haven’t selected any to process yet.')
      );
    }
  }
};
