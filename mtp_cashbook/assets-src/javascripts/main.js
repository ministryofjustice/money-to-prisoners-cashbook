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
      require('feature-tour'),
      require('messages'),
      require('print'),
      require('polyfills'),
      require('running-total'),
      require('select-all'),
      require('sticky-header'),
      require('unload')
    ])
    .init();
}());
