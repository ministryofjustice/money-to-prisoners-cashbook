(function () {
  'use strict';

  require('polyfills').Polyfills.init();
  require('placeholder-polyfill').PlaceholderPolyfill.init();

  // common
  require('proposition-user-menu').PropositionUserMenu.init();
  require('dialogue-box').DialogueBox.init();
  require('messages').Messages.init();
  require('notifications').Notifications.init();
  require('print').Print.init();
  require('select-all').SelectAll.init();
  require('unload').Unload.init();
  require('disclosure').Disclosure.init();
  require('analytics').Analytics.init();
  require('track-printing').TrackPrinting.init();
  require('tabbed-panel').TabbedPanel.init();

  // cashbook
  require('sticky-header').StickyHeader.init();
  require('align-totals').AlignTotals.init();
  require('batch-validation').BatchValidation.init();
  require('running-total').RunningTotal.init();
  require('selection-count').SelectionCount.init();
  require('confirmation-button').ConfirmationButton.init();
  require('confirm-manual').ConfirmManual.init();
  require('print-batch').PrintBatch.init();
  require('navigation').Navigation.init();
  require('sort-code').SortCode.init();
  require('page-contents').PageContents.init();
  require('conditionally-revealed').ConditionallyRevealed.init();
  require('disbursements').Disbursements.init();
}());
