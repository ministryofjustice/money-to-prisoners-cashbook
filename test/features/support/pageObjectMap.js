/* jshint node: true */

'use strict';

var globule = require('globule');
var path = require('path');

var pages = globule.find('./test/features/pages/**/*.js');

for (var i = 0; i < pages.length; i++) {
  var page = require(path.resolve(pages[i]));
  module.exports[page.name] = page.class;
}
