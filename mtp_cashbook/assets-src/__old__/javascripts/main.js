(function () {
  'use strict';

  // common
  require('select-all').SelectAll.init();
  require('unload').Unload.init();
  require('track-printing').TrackPrinting.init();

  // cashbook
  require('sign-up').SignUpChoices.init();
  require('sticky-header').StickyHeader.init();
  require('batch-validation').BatchValidation.init();
  require('selection-count').SelectionCount.init();
  require('confirm-manual').ConfirmManual.init();
  require('navigation').Navigation.init();
}());
