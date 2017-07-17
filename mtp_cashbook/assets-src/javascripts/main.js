(function () {
  'use strict';
  require('polyfills').Polyfills.init();

  require('proposition-header').PropositionHeader.init();
  require('dialogue-box').DialogueBox.init();
  require('collapsing-table').CollapsingTable.init();
  require('messages').Messages.init();
  require('print').Print.init();
  require('select-all').SelectAll.init();
  require('unload').Unload.init();
  require('disclosure').Disclosure.init();
  require('analytics').Analytics.init();
  require('track-printing').TrackPrinting.init();
  require('confirm-manual').ConfirmManual.init();
  require('footer-feedback').FooterFeedback.init();
  require('print-batch').PrintBatch.init();

  require('sticky-header').StickyHeader.init();
  require('align-totals').AlignTotals.init();
  require('batch-validation').BatchValidation.init();
  require('running-total').RunningTotal.init();
  require('selection-count').SelectionCount.init();
  require('confirmation-button').ConfirmationButton.init();
  require('training').Training.init();
}());
