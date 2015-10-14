/* jshint node: true */

'use strict';

var myHooks = function () {

  /**
   * BeforeFeatures handler
   *
   * Provides access to the pagesMap
   * on browser
   *
   * @params {event} event The event being attached to
   * @params {function} callback The callback function of the hook
   */
  this.registerHandler('BeforeFeatures', function (event, callback) {
    browser.pages = require('./pagesMap.js');
    callback();
  });

  /**
   * After hook
   *
   * Run after every scenario to delete cookies and
   * kill each session
   *
   * @params {obj} scenario The scenario that has just been run
   * @params {function} callback The callback function of the hook
   */
  this.After(function(scenario, callback) {
    browser
      .deleteCookie()
      .call(callback);
  });

};

module.exports = myHooks;
