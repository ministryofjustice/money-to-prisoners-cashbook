/* jshint node: true */

'use strict';

var conf = require('./wdio.conf.js');

// ============
// Capabilities
// ============
conf.config.capabilities = [{
  browserName: 'chrome'
}];

// ===================
// Test Configurations
// ===================

// run only work in progress tags
conf.config.cucumberOpts.tags = ['@wip', '~@ignore'];

module.exports = conf;
