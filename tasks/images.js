'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var imagemin = require('gulp-imagemin');

gulp.task('images', ['clean-images'], function() {
  var images = paths.images.concat(paths.vendor_images);

  gulp
    .src(images)
    .pipe(imagemin({ optimizationLevel: 5 }))
    .pipe(gulp.dest(paths.dest + 'images'));
});
