/* jshint node: true */

//
// Gulp tasks are shared across all 3 applications
// and are stored in an NPM Package:
// https://github.com/ministryofjustice/money-to-prisoners-gulp-tasks
//

'use strict';

var gulp = require('gulp');
var argv = require('yargs').argv;
var getTask = require('money-to-prisoners-gulp-tasks');
var webpack = require('webpack');
var gutil = require('gulp-util');

var production = argv.production;

if (!production) {
  var browserSync = require('browser-sync');
}



// paths
var appBase = 'mtp_cashbook/';

var paths = {
  src: appBase + 'assets-src/',
  dest: appBase + 'assets/',
  govukElements: 'node_modules/mojular-govuk-elements/',
  common: 'node_modules/money-to-prisoners-common/assets/'
};

var mojularLoadPaths = require('mojular/sass-paths')([
  require('mojular-govuk-elements/package.json'),
  require('mojular-moj-elements/package.json')
]);

function getLoadPaths () {
  var paths = [
   'node_modules/money-to-prisoners-common/assets/scss',
   'node_modules/breakpoint-sass/stylesheets'
 ];

 return paths;
}


gulp.task('clean:css', getTask('clean', {
  src: paths.dest + 'stylesheets'
}));

gulp.task('clean:images', getTask('clean', {
  src: paths.dest + 'images'
}));

gulp.task('clean:js', getTask('clean', {
  src: paths.dest + 'scripts'
}));

gulp.task('clean', [
  'clean:css',
  'clean:images',
  'clean:js'
]);


gulp.task('sass', ['clean:css'], getTask('scss', {
  src: paths.src + 'stylesheets/**/*.scss',
  dest: paths.dest + 'stylesheets/',
  includePaths: mojularLoadPaths.concat(getLoadPaths()),
  browserSync: production ? browserSync : false
}));

gulp.task('scripts', ['clean:js'], function(callback) {
  webpack(require('./webpack.config.js')).run(function(err, stats) {
    if(err) {
      throw new gutil.PluginError('webpack', err);
    }
    gutil.log('[webpack]', stats.toString({
      colors: true,
      modules: false,
      chunkModules: false
    }));
    callback();
  });
});

gulp.task('lint', getTask('lint', {
  src: [
    paths.src + 'javascripts/**/*.js',
    'gulpfile.js',
    'test/**/*.js'
  ]
}));

gulp.task('minify-scripts', ['lint', 'scripts'], getTask('minify-scripts', {
  src: paths.dest + 'scripts/*.js',
  dest: paths.dest + 'scripts'
}));


gulp.task('images', ['clean:images'], getTask('images', {
  src: [
    paths.src + 'images/**/*',
    paths.govukElements + 'images/**/*',
    paths.common + 'images/**/*',
    paths.hopscotchHighlight + 'images/**/*'
  ],
  dest: paths.dest + 'images'
}));


gulp.task('build', [
  'sass',
  'minify-scripts',
  'images'
]);

if (!production) {
  gulp.task('serve', ['build'], function () {
    var host = argv.host || 'localhost';
    var port = argv.port || 8001;
    var browsersyncPort = argv.browsersyncport || 3000;
    var browsersyncUIPort = argv.browsersyncuiport || 3001;
    var browsersyncReloadDelayed = function() {
      setTimeout(browserSync.reload, 1000);
    };

    browserSync.init({
      proxy: host + ':' + port,
      open: false,
      port: browsersyncPort,
      ui: {
        port: browsersyncUIPort
      }
    });

    gulp.watch('**/templates/**/*').on('change', browsersyncReloadDelayed);
    gulp.watch(paths.src + 'stylesheets/**/*', ['sass-reload']);
    gulp.watch(paths.src + 'images/**', ['img-reload']);
    gulp.watch(paths.src + 'javascripts/**/*.js', ['js-reload']);
    gulp.watch(paths.common + '/**/*.js', ['scripts']);
    if (argv.dirs) {
      argv.dirs.split(':').forEach(function(dir) {
        gulp.watch(dir + '/**/*', ['build-reload']);
      });
    }
    gulp.task('build-reload', ['build'], browsersyncReloadDelayed);
    gulp.task('sass-reload', ['sass'], browsersyncReloadDelayed);
    gulp.task('img-reload', ['images'], browsersyncReloadDelayed);
    gulp.task('js-reload', ['scripts'], browsersyncReloadDelayed);
   });

}

gulp.task('default', ['build']);
