/* jshint node: true */

'use strict';

/*
 * cashboook.js
 *
 * Provides application specific step definitions
 *
 */
var cashbookSteps = function(){

  /**
   * Click on a form checkbox
   *
   * Usage: When I click on checkbox number 4 on form number 1
   *
   * @params {number} formNumber (in document order)
   * @params {number} checkboxNumber in form (in document order)
   * @params {function} next The callback function of the scenario
   */
  this.When(/^I click on the first checkbox$/, function(next) {
    browser.click(
      '//body//form[1]//tr[1]//td[@class="check"][1]/label',
      next
    );
  });

  /**
   * Check that the text is visible in a box
   *
   * Usage: I should see "Do you want to continue" in a dialog box
   * Usage: I should see "Error" in an error box
   *
   * @params {function} text The text of the button to click
   * @params {function} next The callback function of the scenario
   */

  this.Then(
    /^I should see "([^"]+)" in an? (dialog|error) box$/,
    function(text, boxType, next) {
      var selector = (boxType === 'dialog') ? 'dialog h3' : 'div.error-summary h1';
      browser.getText(selector)
        .should.eventually.contain(text)
        .and.notify(next);
    }
  );



};

module.exports = cashbookSteps;
