/* jshint node: true */

'use strict';

/*
 * new_credits.js
 *
 * New credits page object
 * Detaches UI interactions from step definitions
 *
 */
var NewCreditsPage = function (client) {

  this.get = function (callback) {
    client
      .url('/batch')
      .call(callback);
  };

};

module.exports = {
  class: NewCreditsPage,
  name: 'New credits'
};
