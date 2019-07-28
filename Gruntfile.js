const path = require('path');

module.exports = function (grunt) {
    var staticLibPath = path.resolve(
        grunt.config.get('staticDir'), 'built', 'plugins', 'isic_archive', 'libs');

    // Install and copy legacy resources for Angular app
    grunt.registerTask('isic_archive-legacy-bower-install', 'Install Bower packages', function () {
        var bower = require('bower');
        var done = this.async();
        bower.commands
            .install([
                'jquery#2.1.0',
                'flatstrap#3.1.1',
                'font-awesome#4.0.3',
                'angular#1.4.5',
                'angular-resource#1.4.5',
                'angular-ui-bootstrap-bower#0.14.3'
            ])
            .on('end', function (results) {
                done();
            })
            .on('error', function (results) {
                done(false);
            });
    });
    grunt.config.set('copy.isic_archive-legacy-libs-bower', {
        expand: true,
        nonull: true,
        cwd: 'bower_components',
        src: [
            'jquery/dist/jquery.min.js',
            'bootstrap/dist/js/bootstrap.min.js',
            'bootstrap/dist/css/bootstrap.min.css',
            'bootstrap/dist/fonts/glyphicons-halflings-regular.woff',
            'bootstrap/dist/fonts/glyphicons-halflings-regular.ttf',
            'font-awesome/css/font-awesome.min.css',
            'font-awesome/fonts/fontawesome-webfont.ttf',
            'font-awesome/fonts/fontawesome-webfont.woff',
            'angular/angular.min.js',
            'angular-resource/angular-resource.min.js',
            'angular-bootstrap/ui-bootstrap-tpls.min.js'
        ],
        dest: staticLibPath
    });
    grunt.registerTask('isic_archive-legacy', [
        // 'npm-install:isic_archive:false:bower@^1.8.0',
        'isic_archive-legacy-bower-install',
        'copy:isic_archive-legacy-libs-bower'
    ]);

    grunt.registerTask('isic_archive-web', [
        'isic_archive-legacy'
    ]);
};
