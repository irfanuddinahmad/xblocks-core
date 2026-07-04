/* eslint-env node */
const path = require('path');
const webpack = require('webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const defineHeader = /\(function ?\(((define|require|requirejs|\$)(, )?)+\) ?\{/;
const defineCallFooter = /\}\)\.call\(this, ((define|require)( \|\| RequireJS\.(define|require))?(, )?)+?\);/;
const defineDirectFooter = /\}\(((window\.)?(RequireJS\.)?(requirejs|define|require|jQuery)(, )?)+\)\);/;
const defineFancyFooter = /\}\).call\(\s*this[\s\S]*define[\s\S]*\);/;
const defineFooter = new RegExp('(' + defineCallFooter.source + ')|('
    + defineDirectFooter.source + ')|('
    + defineFancyFooter.source + ')', 'm');

module.exports = {
    context: __dirname,

    entry: {
        ProblemBlockDisplay: [
            './static/js/xmodule.js',
            './static/js/javascript_loader.js',
            './static/js/display.js',
            './static/js/collapsible.js',
            './static/js/imageinput.js',
            './static/js/schematic.js'
        ]
    },

    output: {
        filename: '[name].js',
        path: path.resolve(__dirname, '../public/js'),
        library: {
            type: 'window'
        }
    },

    externals: {
        jquery: 'jQuery',
        underscore: '_',
        $: 'jQuery',
        gettext: 'gettext'
    },

    resolve: {
        extensions: ['.js', '.jsx', '.json'],
        alias: {
            'codemirror': path.resolve(__dirname, './static/js/vendor/codemirror-compressed.js'),
            'edx-ui-toolkit': path.resolve(__dirname, '../../../node_modules/edx-ui-toolkit/src/')
        }
    },

    plugins: [
        new webpack.ProvidePlugin({
            _: 'underscore',
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            CodeMirror: 'codemirror',
            'edx.HtmlUtils': 'edx-ui-toolkit/js/utils/html-utils'
        }),
        new CopyWebpackPlugin({
            patterns: [
                {
                    from: './static/css/ProblemBlockDisplay.css',
                    to: path.resolve(__dirname, '../public/css')
                }
            ]
        })
    ],

    module: {
        noParse: [
            /\/codemirror-compressed\.js/
        ],
        rules: [
            {
                test: /\/static\/js\//,
                loader: 'string-replace-loader',
                options: {
                    multiple: [
                        { search: defineHeader, replace: '' },
                        { search: defineFooter, replace: '' },
                        {
                            search: /(\/\* RequireJS) \*\//g,
                            replace(match, p1, offset, string) {
                                return p1;
                            }
                        },
                        {
                            search: /\/\* Webpack/g,
                            replace(match, p1, offset, string) {
                                return match + ' */';
                            }
                        },
                        {
                            search: /text!(.*?\.underscore)/g,
                            replace(match, p1, offset, string) {
                                return p1;
                            }
                        },
                        { search: /RequireJS.require/g, replace: 'require' }
                    ]
                }
            },
            {
                test: /\.(js|jsx)$/,
                exclude: [
                    /node_modules/,
                    /\/static\/js\/(?!(display|imageinput|schematic|collapsible|javascript_loader|xmodule)\.js|vendor\/codemirror-compressed\.js)/
                ],
                use: 'babel-loader'
            },
            {
                test: /codemirror/,
                use: [
                    {
                        loader: 'exports-loader',
                        options: 'window.CodeMirror'
                    },
                ]
            }
        ]
    },
    optimization: {
        minimize: false
    },
    mode: 'development',
    devtool: 'source-map'
};
