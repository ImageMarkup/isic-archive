const path = require('path');
const process = require('process');
const webpack = require('webpack'); // eslint-disable-line import/no-extraneous-dependencies
const SentryWebpackPlugin = require('@sentry/webpack-plugin');
const GitRevisionPlugin = require('git-revision-webpack-plugin');


const gitRevisionPlugin = new GitRevisionPlugin();


module.exports = {
  publicPath: process.env.ISIC_INTEGRATION ? '/' : '/admin/',

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

  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        COMMITHASH: JSON.stringify(gitRevisionPlugin.commithash()),
      }),
      new SentryWebpackPlugin({
        dryRun: process.env.NODE_ENV !== 'production',
        include: './dist/js',
        release: gitRevisionPlugin.commithash(),
        ignoreFile: '.sentrycliignore',
        ignore: ['node_modules', 'vue.config.js'],
        configFile: 'sentry.properties',
      }),
    ],
  },

  chainWebpack: (config) => {
    // Required to make many Girder imports work
    config.plugin('provide')
      .use(webpack.ProvidePlugin, [{
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
      }]);

    // Reduce the size of the Moment package
    config.plugin('moment-locale')
      .use(webpack.ContextReplacementPlugin, [
        /moment[/\\]locale$/,
        /en/,
      ]);

    // Set the HTML title
    config.plugin('html')
      .tap(([args]) => [{
        ...args,
        title: process.env.ISIC_INTEGRATION ? 'ISIC Archive' : 'ISIC Admin',
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
  },
};
