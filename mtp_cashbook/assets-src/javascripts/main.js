(function () {
  'use strict';

  require('polyfills').Polyfills.init();
  require('placeholder-polyfill').PlaceholderPolyfill.init();

  // common
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
  require('hide-long-text').HideLongText.init();
  require('character-count-warning').CharacterCountWarning.init();
  require('mailcheck-warning').MailcheckWarning.init(
    '.mtp-account-management input[type=email]',
    ['justice.gov.uk'],
    ['gov.uk']
  );
  require('mailcheck-warning').MailcheckWarning.init(
    '.mtp-create-disbursement input[type=email]'
  );

  // cashbook
  require('sign-up').SignUpChoices.init();
  require('sticky-header').StickyHeader.init();
  require('batch-validation').BatchValidation.init();
  require('selection-count').SelectionCount.init();
  require('confirm-manual').ConfirmManual.init();
  require('print-batch').PrintBatch.init();
  require('navigation').Navigation.init();
  require('sort-code').SortCode.init();
  require('page-contents').PageContents.init();
  require('conditionally-revealed').ConditionallyRevealed.init();
  require('disbursements').Disbursements.init();
  require('address-picker').AddressPicker.init();
}());
