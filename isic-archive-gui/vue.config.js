const path = require('path');
const process = require('process');
const webpack = require('webpack'); // eslint-disable-line import/no-extraneous-dependencies
const autoprefixer = require('autoprefixer'); // eslint-disable-line import/no-extraneous-dependencies

module.exports = {
  lintOnSave: false,

  devServer: {
    port: 8081,
    proxy: {
      '/api/v1': {
        // Girder API must be running here in development
        target: process.env.API_HOST || 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },

  chainWebpack: (config) => {
    // Alias "@" to the "./src" directory for imports
    config.resolve.alias
      .set('@$', path.resolve(__dirname, 'src'));

    // Required to make many Girder imports work
    config.plugin('provide')
      .use(webpack.ProvidePlugin, [{
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
      }]);

    // Define the GIRDER_VERSION global, which upstream Girder expects
    config.plugin('define')
      .tap(([definitions]) => [{
        GIRDER_VERSION: JSON.stringify({
          git: false,
          SHA: null,
          shortSHA: null,
          date: new Date().toISOString(),
          apiVersion: null,
        }),
        ...definitions,
      }]);

    // Add PegJS loader
    config.module
      .rule('pegjs')
      .test(/\.pegjs$/)
      .use('pegjs-loader')
      .loader('pegjs-loader');

    // Add loader for downloadable files
    config.module
      .rule('download')
      .test(/\.(txt|pdf)$/)
      .use('file-loader')
      .loader('file-loader')
      .options({
        name: 'download/[name].[hash:8].[ext]',
      });

    // Add BibTeX loader
    config.resolveLoader
      .modules
      .prepend(path.resolve(__dirname, 'loaders'));
    config.module
      .rule('bibtex')
      .test(/\.bibtex$/)
      .use('bibtex-loader')
      .loader('bibtex-loader');

    // Modify existing Pug loader
    // For separate Pug files, we want to use the full 'pug-loader'; for inlined Pug segments
    // loaded with vue-loader, continue to use 'pug-plain-loader'
    // See https://vue-loader.vuejs.org/guide/pre-processors.html#pug
    config.module
      .rule('pug')
      .uses
      .delete('pug-plain-loader');
    config.module
      .rule('pug')
      .oneOf('pug-vue')
      .resourceQuery(/^\?vue/)
      .use('pug-plain-loader')
      .loader('pug-plain-loader');
    config.module
      .rule('pug')
      .oneOf('pug-file')
      .use('pug-loader')
      .loader('pug-loader');

    // postcss-loader is not picking up the config within 'package.json', causing errors
    // This seems to work around the issue
    // See: https://github.com/postcss/postcss-loader/issues/204
    config.module
      .rule('stylus')
      .oneOf('normal')
      .use('postcss-loader')
      .tap(options => ({
        ...options,
        ident: 'postcss',
        plugins: () => [
          autoprefixer(),
        ],
      }));
    config.module
      .rule('css')
      .oneOf('normal')
      .use('postcss-loader')
      .tap(options => ({
        ...options,
        ident: 'postcss',
        plugins: () => [
          autoprefixer(),
        ],
      }));
  },
};
