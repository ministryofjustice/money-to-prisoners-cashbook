/* jshint node: true */

'use strict';

var testUsername = 'test_prison_1';
var testPassword = 'test_prison_1';

var SigninPage = function (World) {
  this.usernameLocator = { name: 'username' };
  this.passwordLocator = { name: 'password' };
  this.submitLocator = { name: 'signin' };
  this.signoutLocator = { linkText: 'Sign out' };

  this.get = function (callback) {
    World.visit('auth/login/', callback);
  };

  this.fillForm = function (username, password, callback) {
    World.driver
      .findElement(this.usernameLocator)
      .sendKeys(username);

    World.driver
      .findElement(this.passwordLocator)
      .sendKeys(password);

    World.driver
      .findElement(this.submitLocator)
      .click()
      .then(function() {
        callback();
      });
  };

  this.signin = function (callback) {
    var _this = this;

    _this.get(function () {
      _this.fillForm(testUsername, testPassword, callback);
    });
  };

  this.signinWith = function (username, password, callback) {
    this.fillForm(username, password, callback);
  };

  this.signout = function (callback) {
    World.visit('auth/logout/', callback);
  };

};

module.exports = {
  class: SigninPage,
  name: 'Sign in'
};
