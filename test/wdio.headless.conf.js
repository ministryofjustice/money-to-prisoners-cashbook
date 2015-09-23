/* jshint node: true */

'use strict';

var conf = require('./wdio.conf.js');

// ============
// Capabilities
// ============
conf.config.capabilities = [{
  browserName: 'phantomjs'
}];

module.exports = conf;
