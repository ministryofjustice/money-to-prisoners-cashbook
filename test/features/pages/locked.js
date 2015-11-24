/* jshint node: true */

'use strict';

/*
 * locked.js
 *
 * Locked payments page object
 * Detaches UI interactions from step definitions
 *
 */
var LockedPaymentsPage = function (client) {

  this.get = function (callback) {
    client
      .url('/locked')
      .call(callback);
  };

};

module.exports = {
  class: LockedPaymentsPage,
  name: 'Locked payments'
};
