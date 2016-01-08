/* globals require */

(function() {
  'use strict';

  var Mojular = require('mojular');

  Mojular
    .use([
      require('mojular-govuk-elements'),
      require('mojular-moj-elements'),
      require('dialog'),
      require('batch-validation'),
      require('show-hide'),
      require('messages'),
      require('print'),
      require('polyfills'),
      require('select-all'),
      require('unload'),
      require('help-popup'),

      require('sticky-header'),
      require('running-total')
    ])
    .init();
}());
