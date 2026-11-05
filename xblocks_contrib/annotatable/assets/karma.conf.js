/* eslint-env node */
'use strict';

module.exports = function (config) {
    config.set({
        basePath: '',

        frameworks: ['jasmine'],

        files: [
            { pattern: require.resolve('jquery/dist/jquery.js'), included: true },
            { pattern: require.resolve('jasmine-jquery/lib/jasmine-jquery.js'), included: true },

            { pattern: 'spec_helpers/*.js', included: true },

            { pattern: '../static/js/src/annotatable.js', included: true },

            { pattern: 'fixtures/**/*.html', included: false, served: true },

            { pattern: 'spec/*_spec.js', included: true }
        ],

        plugins: [
            'karma-jasmine',
            'karma-firefox-launcher',
            require('karma-spec-reporter')
        ],

        reporters: ['spec'],

        port: 9876,
        colors: true,
        logLevel: config.LOG_INFO,
        autoWatch: false,
        browsers: ['FirefoxNoUpdates'],

        customLaunchers: {
            FirefoxNoUpdates: {
                base: 'Firefox',
                prefs: {
                    'app.update.auto': false,
                    'app.update.enabled': false
                }
            }
        },

        singleRun: true,
        concurrency: Infinity,
        client: { captureConsole: true }
    });
};
