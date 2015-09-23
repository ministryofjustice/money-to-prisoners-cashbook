/* jshint node: true */

'use strict';

var globule = require('globule');
var path = require('path');
var pages = globule.find('./test/features/pages/**/*.js');
var pageMap = {};

for (var i = 0; i < pages.length; i++) {
  var pagePath = path.resolve(pages[i]);
  var page = require(pagePath);

  pageMap[page.name] = page.class;
}

module.exports = pageMap;
