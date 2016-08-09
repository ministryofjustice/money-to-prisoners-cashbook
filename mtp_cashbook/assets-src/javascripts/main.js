/* globals require */

(function() {
  'use strict';

  require('dialog').Dialog.init();
  require('collapsing-table').CollapsingTable.init();
  require('messages').Messages.init();
  require('print').Print.init();
  require('polyfills').Polyfills.init();
  require('select-all').SelectAll.init();
  require('unload').Unload.init();
  require('help-popup').HelpPopup.init();
  require('analytics').Analytics.init();
  require('track-printing').TrackPrinting.init();

  require('batch-validation').BatchValidation.init();
  require('sticky-header').StickyHeader.init();
  require('running-total').RunningTotal.init();
  require('search-focus').SearchFocus.init();
  require('training').Training.init();
}());
