/**
 * Copyright 2016 Kitware Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

module.exports = function (grunt) {
    var path = require('path');

    // This gruntfile is only designed to be used with girder's build system.
    // Fail if grunt is executed here.
    if (path.resolve(__dirname) === path.resolve(process.cwd())) {
        grunt.fail.fatal('To build isic_archive, run grunt from Girder\'s root directory');
    }

    var fs = require('fs');
    var defaultTasks = [];

    // Since this is an external web app in a plugin,
    // it handles building itself
    //
    // It is not included in the plugins being built by virtue of
    // the web client not living in web_client, but rather web_external
    var configureIsicArchive = function () {
        var pluginDir = 'plugins/isic_archive';
        var staticDir = 'clients/web/static/built/plugins/isic_archive';
        var files;

        if (!fs.existsSync(staticDir)) {
            fs.mkdirSync(staticDir);
        }

        // External app Jade templates
        var jadeDir = pluginDir + '/web_external/templates';
        files = {};
        files[staticDir + '/isic_archive_templates.js'] = [
            jadeDir + '/**/*.jade'
        ];
        grunt.config.set('jade.isic_archive', {
            files: files
        });
        grunt.config.set('jade.isic_archive.options', {
            namespace: 'isic.templates'
        });
        grunt.config.set('watch.jade_isic_archive_app', {
            files: [jadeDir + '/**/*.jade'],
            tasks: ['jade:isic_archive', 'uglify:isic_archive']
        });
        defaultTasks.push('jade:isic_archive');

        // External app Stylus stylesheets
        var cssDir = pluginDir + '/web_external/stylesheets';
        files = {};
        files[staticDir + '/isic_archive.app.min.css'] = [
            cssDir + '/**/*.styl'
        ];
        grunt.config.set('stylus.isic_archive', {
            files: files
        });
        grunt.config.set('watch.stylus_isic_archive_app', {
            files: [cssDir + '/**/*.styl'],
            tasks: ['stylus:isic_archive']
        });
        defaultTasks.push('stylus:isic_archive');

        // External app JS app
        var jsDir = pluginDir + '/web_external/js';
        files = {};
        // name this isic_archive.app.min.js instead of plugin.min.js
        // so that girder app won't load isic_archive, which
        // should only be loaded as a separate web app running as isic_archive
        files[staticDir + '/isic_archive.app.min.js'] = [
            jsDir + '/init.js',
            staticDir + '/isic_archive_templates.js',
            jsDir + '/view.js',
            jsDir + '/app.js',
            jsDir + '/models/**/*.js',
            jsDir + '/collections/**/*.js',
            jsDir + '/views/**/*.js'
        ];
        files[staticDir + '/main.min.js'] = [
            jsDir + '/main.js'
        ];
        grunt.config.set('uglify.isic_archive', {
            files: files
        });
        grunt.config.set('watch.js_isic_archive_app', {
            files: [jsDir + '/**/*.js'],
            tasks: ['uglify:isic_archive']
        });
        defaultTasks.push('uglify:isic_archive');

        // External app extra files
        var extraDir = pluginDir + '/web_external/extra';
        grunt.config.set('copy.isic_archive', {
            expand: true,
            cwd: pluginDir + '/web_external',
            src: ['extra/**'],
            dest: staticDir
        });
        grunt.config.set('watch.copy_isic_archive', {
            files: [extraDir + '/**/*'],
            tasks: ['copy:isic_archive']
        });
        defaultTasks.push('copy:isic_archive');

        // Angular app Bower packages
        grunt.config.set('copy.isic_archive_bower_libs', {
            expand: true,
            cwd: pluginDir + '/bower_components',
            src: [
                'jquery/dist/jquery.min.js',
                'underscore/underscore-min.js',
                'flatstrap/dist/js/bootstrap.min.js',
                'flatstrap/dist/css/bootstrap.min.css',
                'flatstrap/dist/fonts/glyphicons-halflings-regular.woff',
                'flatstrap/dist/fonts/glyphicons-halflings-regular.ttf',
                'font-awesome/css/font-awesome.min.css',
                'font-awesome/fonts/fontawesome-webfont.ttf',
                'font-awesome/fonts/fontawesome-webfont.woff',
                'angular/angular.min.js',
                'angular-resource/angular-resource.min.js',
                'angular-ui-bootstrap-bower/ui-bootstrap-tpls.min.js'
            ],
            dest: staticDir + '/libs'
        });
        defaultTasks.push('copy:isic_archive_bower_libs');

        // External app JS and CSS libraries
        files = {};
        files[staticDir + '/isic_archive.ext.min.js'] = [
            pluginDir + '/bower_components/pegjs/peg-0.10.0.min.js',
            pluginDir + '/node_modules/select2/dist/js/select2.min.js',
            pluginDir + '/node_modules/geojs/geo.min.js'
        ];
        files[staticDir + '/isic_archive.ext.min.css'] = [
            pluginDir + '/node_modules/select2/dist/css/select2.min.css',
            pluginDir + '/node_modules/select2-bootstrap-theme/dist/select2-bootstrap.min.css'
        ];
        grunt.config.set('concat.isic_archive', {
            files: files
        });
        grunt.config.set('concat.isic_archive.options', {
            stripBanners: false
        });
        defaultTasks.push('concat:isic_archive');
    };

    configureIsicArchive();
    grunt.registerTask('isic_archive-web', defaultTasks);
};
