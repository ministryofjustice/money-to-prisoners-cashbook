/* jshint node: true */

'use strict';

var gulp = require('gulp');
var requireDir = require('require-dir');

requireDir('./tasks/common');

gulp.task('build', [
  'minify-css',
  'minify-scripts',
  'images'
]);

gulp.task('default', ['build']);
