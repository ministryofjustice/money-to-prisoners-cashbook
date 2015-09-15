/* jshint node: true */

'use strict';

var authSteps = function(){
  this.World = require('../support/world').World;

  this.Before(function (callback) {
    this.SigninPage = new this.pageObjects['Sign in'](this);
    callback();
  });

  this.Given(/^I am signed in$/, function(next) {
    this.SigninPage.signin(next);
  });

  this.When(/^I sign in with "([^"]*)" and "([^"]*)"$/, function (username, password, next) {
    this.SigninPage.signinWith(username, password, next);
  });

  this.When(/^I sign out$/, function (next) {
    this.SigninPage.signout(next);
  });
};

module.exports = authSteps;
