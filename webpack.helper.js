const path = require('path');

const ExtractTextPlugin = require('extract-text-webpack-plugin');

module.exports = function (baseConfig, helperConfig) {
    if (helperConfig.output === 'app') {
        // Don't use any Dll*Plugins
        baseConfig.plugins = [
            new ExtractTextPlugin({
                filename: `${helperConfig.output}.min.css`,
                allChunks: true
            })
        ];

        // Add loader rules for additional types
        baseConfig.module.rules.unshift(
            {
                resource: {
                    test: /\.(pdf|txt)$/
                },
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: 'assets/[name]-[hash:8].[ext]'
                        }
                    }
                ]
            },
            {
                resource: {
                    test: /\.pegjs$/
                },
                use: [
                    'raw-loader'
                ]
            },
            {
                resource: {
                    test: /\.bibtex$/
                },
                use: [
                    'bibtex-loader'
                ]
            }
        );

        // Search for Webpack loaders in this plugin directory first
        baseConfig.resolveLoader.modules.unshift(
            path.resolve(helperConfig.pluginDir, 'loaders')
        );

        // Statically set publicPath, as upstream Girder tries to set this dynamically
        baseConfig.output.publicPath = '/static/built/plugins/isic_archive/';
    }

    return baseConfig;
};
