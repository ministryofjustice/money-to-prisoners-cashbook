/* jshint node: true */

'use strict';

var fs = require('fs');
var path = require('path');
var del = require('del');
var Q = require('q');
var request = require('request');
var selenium = require('selenium-standalone');
var screenshotPath = path.join('test', 'errorshots');


/**
 * Start a selenium server if it doesn't exist
 *
 * @returns {promise} A deferred promise
 */
function startSelenium () {
  var deferred = Q.defer();
  var statusUrl = 'http://localhost:4444/wd/hub/status';

  request(statusUrl, function (error) {
    // selenium not started, start it
    if (error) {
      selenium.install({}, function (err) {
        if (err) { deferred.reject(err); }

        selenium.start(function (err, child) {
          if (err) { deferred.reject(err); }

          selenium.child = child;
          deferred.resolve();
        });
      });
    }

    // already started, return promise
    deferred.resolve();
  });

  return deferred.promise;
}


var config = {

  // ==========
  // Test Files
  // ==========
  specs: [
    './test/features/**/*.feature'
  ],

  // ============
  // Capabilities
  // ============
  capabilities: [{
    browserName: 'chrome'
  }, {
    browserName: 'firefox'
  }, {
    browserName: 'phantomjs'
  }],

  // ===================
  // Test Configurations
  // ===================
  logLevel: 'silent',
  screenshotPath: screenshotPath,
  baseUrl: process.env.WDIO_BASEURL || 'http://localhost:8001',
  framework: 'cucumber',
  reporter: 'dot',
  cucumberOpts: {
    require: [
      './test/features/steps/**/*.js',
      './test/features/pages/**/*.js',
      './test/features/support/**/*.js'
    ],
    // Enable this config to treat undefined definitions as warnings.
    ignoreUndefinedDefinitions: false,
    // run only certain scenarios annotated by tags
    tags: ['~@ignore']
  },

  // =====
  // Hooks
  // =====
  onPrepare: function() {
    // setup screenshot directory
    del.sync(screenshotPath);
    fs.mkdirSync(screenshotPath);

    // start selenium
    return startSelenium();
  },
  before: function() {
    // setup chai-as-promised support
    // http://webdriver.io/guide/testrunner/frameworks.html
    var chai = require('chai');
    var chaiAsPromised = require('chai-as-promised');
    chai.use(chaiAsPromised);
    chai.Should();
  },
  onComplete: function() {
    // shutdown selenium server
    if (selenium.child) {
      selenium.child.kill();
    }
  }

};

module.exports.config = config;
