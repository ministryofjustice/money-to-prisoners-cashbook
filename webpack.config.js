/* jshint node: true */

var webpack = require('webpack');

module.exports = {
  entry: {
//    app: './node_modules/money-to-prisoners-common/assets/javascripts/moj-main.js',
    app: './mtp_cashbook/assets-src/javascripts/main.js',
    polyfills: ['JSON2', 'html5shiv']
  },
  output: {
    path: './mtp_cashbook/assets/scripts',
    filename: '[name].bundle.js'
  },
  module: {
    loaders: [
      { include: /\.json$/, loaders: ['json-loader'] }
    ],
    noParse: [
      /\.\/node_modules\/checked-polyfill\/checked-polyfill\.js$/
   ]
  },
  resolve: {
    root: [
      __dirname + '/node_modules',
      __dirname + '/node_modules/mojular-moj-elements/node_modules'
    ],
    modulesDirectories: [
      'node_modules',
      'node_modules/money-to-prisoners-common/assets/javascripts/modules'
    ],
    extensions: ['', '.json', '.js']
  },
  plugins: [
    new webpack.optimize.DedupePlugin(),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery'
    })
  ]
};
