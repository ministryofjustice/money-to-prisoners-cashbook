/* jshint node: true */

//
// Gulp tasks are shared across all 3 applications
// and are stored in an NPM Package:
// https://github.com/ministryofjustice/money-to-prisoners-gulp-tasks
//

'use strict';

var gulp = require('gulp');
var path = require('path');
var nconf = require('nconf');
var argv = require('yargs').argv;
var mainBowerFiles = require('main-bower-files');
var getTask = require('money-to-prisoners-gulp-tasks');

var production = argv.production;

if (!production) {
  var browserSync = require('browser-sync');
}



// paths
var vendorFiles = mainBowerFiles();
var appBase = 'mtp_cashbook/';
var src = appBase + 'assets-src/';
var dest = appBase + 'assets/';


function getBowerDir () {
  nconf
    .file({ file: './.bowerrc' })
    .load();

  return path.join(process.cwd(), nconf.get('directory'));
}

function getModulePaths (module) {
  var modulePath = path.join(getBowerDir(), module, 'paths.json');
  var obj = require(modulePath);

  /* jshint camelcase: false */
  return obj.import_paths;
}

function getLoadPaths () {
  var bowerDir = getBowerDir();
  var govukImportPaths = getModulePaths('govuk-template');
  var mojularImportPaths = getModulePaths('mojular');
  var mtpImportPaths = getModulePaths('money-to-prisoners-common');
  var joined = govukImportPaths.concat(mojularImportPaths).concat(mtpImportPaths);

  joined = joined.map(function(originalPath) {
    return path.join(bowerDir, originalPath);
  });

  return joined.concat(bowerDir);
}


gulp.task('clean:css', getTask('clean', {
  src: dest + 'stylesheets'
}));

gulp.task('clean:images', getTask('clean', {
  src: dest + 'images'
}));

gulp.task('clean:js', getTask('clean', {
  src: dest + 'javascripts'
}));

gulp.task('clean', [
  'clean:css',
  'clean:images',
  'clean:js'
]);


gulp.task('sass', ['clean:css'], getTask('scss', {
  src: src + 'stylesheets/**/*.scss',
  dest: dest + 'stylesheets/',
  includePaths: getLoadPaths(),
  browserSync: production ? browserSync : false
}));

gulp.task('minify-css', ['sass'], getTask('minify-css', {
  src: dest + 'stylesheets/**/*.css',
  dest: dest + 'stylesheets'
}));


gulp.task('scripts', ['clean:js'], getTask('concat-scripts', {
  src: vendorFiles.concat([
    src + 'bower_components/checked-polyfill/checked-polyfill.js',
    src + 'javascripts/**/*.js',
  ]),
  dest: dest + 'javascripts'
}));

gulp.task('lint', getTask('lint', {
  src: [
    src + 'javascripts/**/*.js',
    'gulpfile.js',
    'test/**/*.js'
  ]
}));

gulp.task('minify-scripts', ['lint', 'scripts'], getTask('minify-scripts', {
  src: dest + 'javascripts/*.js',
  dest: dest + 'javascripts'
}));


gulp.task('images', ['clean:images'], getTask('images', {
  src: [
    src + 'images/**/*',
    src + 'bower_components/hopscotch-highlight/src/images/**/*'
  ],
  dest: dest + 'images'
}));


gulp.task('build', [
  'minify-css',
  'minify-scripts',
  'images'
]);

if (!production) {
  gulp.task('serve', ['build'], function () {
    var host = argv.host || 'localhost';
    var port = argv.port || 8001;
    var browsersyncPort = argv.browsersyncport || 3000;
    var browsersyncUIPort = argv.browsersyncuiport || 3001;

    browserSync.init({
      proxy: host + ':' + port,
      open: false,
      port: browsersyncPort,
      ui: {
        port: browsersyncUIPort
      }
    });

    gulp.watch('**/templates/**/*').on('change', browserSync.reload);
    gulp.watch(src + 'stylesheets/**/*', ['sass']);
    gulp.watch(src + 'images/**', ['img-watch']);
    gulp.watch(src + 'javascripts/**/*.js', ['js-watch']);
  });

  gulp.task('img-watch', ['images'], browserSync.reload);
  gulp.task('js-watch', ['scripts'], browserSync.reload);
}

gulp.task('default', ['build']);
