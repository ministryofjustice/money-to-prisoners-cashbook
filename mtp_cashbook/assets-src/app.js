'use strict';

// design systems
import {initAll} from 'govuk-frontend';
initAll();

// mtp-common
import {Analytics} from 'mtp/components/analytics';
import {Banner} from 'mtp/components/banner';
import {DatePicker} from 'mtp/components/date-picker-field';
import {DialogueBox} from 'mtp/components/dialogue-box';
import {HiddenLongText} from 'mtp/components/hidden-long-text';
import {MailcheckWarning} from 'mtp/components/mailcheck-warning';
import {TabbedPanel} from 'mtp/components/tabbed-panel';

Analytics.init();
Banner.init();
DatePicker.init();
DialogueBox.init();
HiddenLongText.init();
MailcheckWarning.init(
  '.mtp-account-management input[type=email]',
  ['justice.gov.uk'],
  ['gov.uk'],
  []
);
MailcheckWarning.init(
  '#change-your-email #id_email',
  ['gov.sscl.com', 'justice.gov.uk'],
  ['gov.sscl.com', 'gov.uk'],
  []
);
MailcheckWarning.init(
  '.mtp-create-disbursement input[type=email]'
);
TabbedPanel.init();

/*
// common
require('print').Print.init();
require('select-all').SelectAll.init();
require('unload').Unload.init();
require('track-printing').TrackPrinting.init();
require('tabbed-panel').TabbedPanel.init();
require('character-count-warning').CharacterCountWarning.init();

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
*/
