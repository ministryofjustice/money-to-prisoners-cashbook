(function () {
  'use strict';

  // common
  require('unload').Unload.init();
  require('track-printing').TrackPrinting.init();

  // cashbook
  require('sign-up').SignUpChoices.init();
  require('navigation').Navigation.init();
}());
