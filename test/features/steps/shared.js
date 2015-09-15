/* jshint node: true */

'use strict';

var expect = require('chai').expect;

/*
 * shared.js
 *
 * Provides shared step definitions
 *
 */
var sharedSteps = function(){
  this.World = require('../support/world').World;

  /**
   * Go to a url of a page object
   *
   * Usage: Given I am on the "Signin" page
   * Usage: Given I go to the "Signin" page
   *
   * @params {string} page The requested page object name
   * @params {function} next The callback function of the scenario
   */
  this.Given(/^I (?:am on|go to) the "([^"]*)" page$/, function(pageName, next) {
    if (!this.pageObjects[pageName]) {
      throw new Error('Could not find page with name "' + pageName + '" in the PageObjectMap, did you remember to add it?');
    }

    var page = new this.pageObjects[pageName](this);
    page.get(next);
  });

  /**
   * Check the current body content contains
   * supplied text
   *
   * Usage: Then I should see "some text"
   *
   * @params {string} text The text to check for
   * @params {function} next The callback function of the scenario
   */
  this.Then(/^I should see "([^"]*)"$/, function(text, next) {
    this.driver
      .findElement({css: 'body'})
      .getText()
      .then(function (result) {
        expect(result).to.contain(text);
        next();
      });
  });

  /**
   * Check the current body content does not
   * contain supplied text
   *
   * Usage: Then I should not see "some text"
   *
   * @params {string} text The text to check on
   * @params {function} next The callback function of the scenario
   */
  this.Then(/^I should not see "([^"]*)"$/, function(text, next) {
    this.driver
      .findElement({css: 'body'})
      .getText()
      .then(function (result) {
        expect(result).not.to.contain(text);
        next();
      });
  });

  /**
   * Check the current page title matches
   * supplied title
   *
   * Usage: Then I should "some title" as the page title
   *
   * @params {string} text The title to check for
   * @params {function} next The callback function of the scenario
   */
  this.Then(/^I should see "([^"]*)" as the page title$/, function(title, next) {
    this.driver
      .getTitle()
      .then(function(result) {
        expect(result).to.equal(title);
        next();
      });
  });
};

module.exports = sharedSteps;
