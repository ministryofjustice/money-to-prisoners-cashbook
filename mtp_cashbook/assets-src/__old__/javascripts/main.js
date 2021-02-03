(function () {
  'use strict';

  // common
  require('unload').Unload.init();
  require('track-printing').TrackPrinting.init();

  // cashbook
  require('sign-up').SignUpChoices.init();
  require('sticky-header').StickyHeader.init();
  require('batch-validation').BatchValidation.init();
  require('navigation').Navigation.init();
}());
