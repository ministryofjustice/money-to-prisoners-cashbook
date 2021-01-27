'use strict';

// design systems
import {initAll} from 'govuk-frontend';
initAll();

// mtp common components
import {initDefaults} from 'mtp_common';
import {initStaffDefaults} from 'mtp_common/staff-app';
import {Card} from 'mtp_common/components/card';
import {MailcheckWarning} from 'mtp_common/components/mailcheck-warning';
initDefaults();
initStaffDefaults();
Card.init();
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
  '.mtp-create-disbursement input[type=email]'
);
