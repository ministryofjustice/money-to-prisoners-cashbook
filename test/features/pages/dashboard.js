/* jshint node: true */

'use strict';

/*
 * dashboard.js
 *
 * Dashboard page object
 * Detaches UI interactions from step definitions
 *
 */
var DashboardPage = function (client) {

  this.get = function (callback) {
    client
      .url('/')
      .call(callback);
  };

};

module.exports = {
  class: DashboardPage,
  name: 'Dashboard'
};
