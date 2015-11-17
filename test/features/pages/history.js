/* jshint node: true */

'use strict';

/*
 * history.js
 *
 * History page object
 * Detaches UI interactions from step definitions
 *
 */
var HistoryPage = function (client) {

  this.get = function (callback) {
    client
      .url('/history')
      .call(callback);
  };

};

module.exports = {
  class: HistoryPage,
  name: 'History'
};
