/* jshint node: true */

'use strict';

/*
 * signin.js
 *
 * Sign in page object
 * Detaches UI interactions from step definitions
 *
 */

var testUsername = 'test_prison_1';
var testPassword = 'test_prison_1';

var SigninPage = function () {
  this.usernameField = '#id_username';
  this.passwordField = '#id_password';
  this.signinForm = '#login-form';

  this.get = function (callback) {
    browser
      .url('/login/')
      .call(callback);
  };

  this.fillForm = function (username, password, callback) {
    browser
      .setValue(this.usernameField, username)
      .setValue(this.passwordField, password)
      .submitForm(this.signinForm)
      .call(callback);
  };

  this.signin = function (callback) {
    var that = this;

    this.get(function () {
      that.fillForm(testUsername, testPassword, callback);
    });
  };

  this.signinWith = function (username, password, callback) {
    this.fillForm(username, password, callback);
  };

  this.signout = function (callback) {
    browser
      .url('/logout/')
      .call(callback);
  };

};

module.exports = {
  class: SigninPage,
  name: 'Sign in'
};
