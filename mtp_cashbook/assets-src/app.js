'use strict';

// design systems
import {initAll} from 'govuk-frontend';
initAll();

// mtp common components
import {initDefaults} from 'mtp_common';
import {initStaffDefaults} from 'mtp_common/staff-app';
import {BeforeUnload} from 'mtp_common/components/before-unload';
import {Card} from 'mtp_common/components/card';
import {DialogueBox} from 'mtp_common/components/dialogue-box';
import {HiddenLongText} from 'mtp_common/components/hidden-long-text';
import {MailcheckWarning} from 'mtp_common/components/mailcheck-warning';
import {PageContents} from 'mtp_common/components/page-contents';
import {PrintTrigger} from 'mtp_common/components/print-trigger';
import {TabbedPanel} from 'mtp_common/components/tabbed-panel';
initDefaults();
initStaffDefaults();
BeforeUnload.init();
Card.init();
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
  ['justice.gov.uk'],
  ['gov.uk'],
  []
);
MailcheckWarning.init(
  '.mtp-email-input--disbursements'
);
PageContents.init();
PrintTrigger.init();
TabbedPanel.init();

// app components
import {Cashbook} from './components/cashbook';
import {Disbursements} from './components/disbursements';
import {PrintLinkTarget} from './components/print-link-target';
import {RadioReveal} from './components/radio-reveal';
Cashbook.init();
Disbursements.init();
PrintLinkTarget.init();
RadioReveal.init();
