/* jshint node: true */

'use strict';

/*
 * auth.js
 *
 * Provides auth specific step definitions
 *
 */
var authSteps = function(){

  /**
   * Make Sign in page object to every defintion
   *
   * @params {function} callback The callback function of the scenario
   */
  this.Before(function (callback) {
    this.SigninPage = new browser.pages['Sign in']();
    callback();
  });

  /**
   * Sign in using test account
   *
   * Usage: Given I am signed in
   *
   * @params {function} next The callback function of the scenario
   */
  this.Given(/^I am signed in$/, function(next) {
    this.SigninPage.signin(next);
  });

  /**
   * Sign in using test account
   *
   * Usage: When I sign in with "my_username" and "my_password"
   *
   * @params {string} username The username to sign in with
   * @params {string} password The password to sign in with
   * @params {function} next The callback function of the scenario
   */
  this.When(/^I sign in with "([^"]*)" and "([^"]*)"$/, function (username, password, next) {
    this.SigninPage.signinWith(username, password, next);
  });

  /**
   * Sign out of the current account
   *
   * Usage: When I sign out
   *
   * @params {function} next The callback function of the scenario
   */
  this.When(/^I sign out$/, function (next) {
    this.SigninPage.signout(next);
  });

};

module.exports = authSteps;
