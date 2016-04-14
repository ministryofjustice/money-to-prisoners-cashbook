/* globals require */

(function() {
  'use strict';

  var Mojular = require('mojular');

  Mojular
    .use([
      require('mojular-govuk-elements'),
      require('mojular-moj-elements'),
      require('dialog'),
      require('show-hide'),
      require('messages'),
      require('print'),
      require('polyfills'),
      require('select-all'),
      require('unload'),
      require('help-popup'),
      require('analytics'),

      require('batch-validation'),
      require('sticky-header'),
      require('running-total'),
      require('search-focus'),
      require('copy-to-clipboard')
    ])
    .init();
}());
