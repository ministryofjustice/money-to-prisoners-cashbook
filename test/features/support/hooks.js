/* jshint node: true */

'use strict';

var driver = require('./world.js').driver;
var fs = require('fs');
var path = require('path');
var del = require('del');
var sanitize = require('sanitize-filename');
var screenshotPath = './test/screenshots';

var myHooks = function () {

  this.After(function(scenario, callback) {
    if(scenario.isFailed()) {
      this.driver.takeScreenshot().then(function(data){
        var base64Data = data.replace(/^data:image\/png;base64,/,'');
        var filename = sanitize(scenario.getName() + '.png').replace(/ /g,'-');
        var filepath = path.join(screenshotPath, filename);

        fs.writeFile(filepath, base64Data, 'base64', function(err) {
          if (err) {
            console.log(err);
          }
        });
      });
    }

    this.driver.manage().deleteAllCookies()
      .then(function() {
        callback();
      });
  });

  this.registerHandler('BeforeFeatures', function (event, callback) {
    del.sync(screenshotPath);

    if(!fs.existsSync(screenshotPath)) {
      fs.mkdirSync(screenshotPath);
    }

    callback();
  });

  this.registerHandler('AfterFeatures', function (event, callback) {
    driver
      .quit()
      .then(function () {
        callback();
      });
  });

};

module.exports = myHooks;
