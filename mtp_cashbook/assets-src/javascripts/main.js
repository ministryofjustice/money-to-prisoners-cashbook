/* globals require, console */

(function() {
  'use strict';

  var Mojular = require('mojular');

  Mojular
    .use([
      require('mojular-govuk-elements'),
      require('mojular-moj-elements'),
      require('dialog'),
      require('batch-validation'),
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

  var moduleNames = Object.keys(Mojular.Modules);
  if(moduleNames.length) {
    var moduleList = moduleNames.map(function(i) {
      return '• ' + i;
    }).join('\n').replace(/^\s+/, '');
    console.log('The following modules are loaded:\n' + moduleList);
  }
}());
