/* globals require */

(function() {
  'use strict';

  require('proposition-header').PropositionHeader.init();
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

  require('sticky-header').StickyHeader.init();
  require('align-totals').AlignTotals.init();
  require('batch-validation').BatchValidation.init();
  require('running-total').RunningTotal.init();
  require('confirmation-button').ConfirmationButton.init();
  require('search-focus').SearchFocus.init();
  require('training').Training.init();
  require('selection-buttons').SelectionButtons.init();
}());
