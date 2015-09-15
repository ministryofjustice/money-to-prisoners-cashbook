/* jshint node: true */

'use strict';

var webdriver = require('selenium-webdriver');

var buildDriver = function() {
  return new webdriver.Builder()
    .forBrowser('phantomjs')
    .build();
};

var driver = buildDriver();

var World = function World(callback) {
  var defaultTimeout = 20000;

  this.webdriver = webdriver;
  this.driver = driver;

  this.waitFor = function(cssLocator, timeout) {
    var waitTimeout = timeout || defaultTimeout;
    return driver.wait(function() {
      return driver.isElementPresent({ css: cssLocator });
    }, waitTimeout);
  };

  this.page = function(path){
   return 'http://localhost:3000/' + path;
  };

  this.visit = function(path, callback){
    this.driver
      .get(this.page(path))
      .then(function () {
        callback();
      });
  };

  this.pageObjects = require('./pageObjectMap.js');

  callback();
};

module.exports.World = World;
module.exports.driver = driver;
