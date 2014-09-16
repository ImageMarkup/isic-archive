﻿/// <reference path="../lib/jasmine-1.3.0/jasmine.js" />
/// <reference path="../../lib/angular.1.2.1.js" />
/// <reference path="../../lib/angular-mocks.1.2.1.js" />
/// <reference path="../../lib/jquery-1.8.2.intellisense.js" />

describe("Testing Acute Select Directive", function () {
    var $scope,
        $compile,
        $timeout;

    var keyCodes = {
        'backspace': 8,
        'tab': 9,
        'enter': 13,
        'escape': 27,
        'pageUp': 33,
        'pageDown': 34,
        'end': 35,
        'home': 36,
        'leftArrow': 37,
        'upArrow': 38,
        'rightArrow': 39,
        'downArrow': 40,
        'del': 46
    };

    beforeEach(function () {
        //load the module
        module('acute.select');

        inject(function (_$compile_, $rootScope, $templateCache, _$timeout_) {

            // Create a scope
            $scope = $rootScope.$new();

            $timeout = _$timeout_;

            // Data for the select
            $scope.colours = [
              { name: 'black', shade: 'dark' },
              { name: 'white', shade: 'light' },
              { name: 'red', shade: 'dark' },
              { name: 'blue', shade: 'dark' },
              { name: 'yellow', shade: 'light' }
            ];

            $compile = _$compile_;

            var directiveTemplate = null;
            var req = new XMLHttpRequest();
            req.onload = function () {
                directiveTemplate = this.responseText;
            };

            // Using 'false' as the third parameter to open() makes the operation synchronous.
            req.open("get", "../acute.select/template/acute.select.htm", false);
            req.send();
            $templateCache.put("/acute.select/acute.select.htm", directiveTemplate);
        });
    });

    it("Creates a UL dropdown and selects 'Red' when 'r' is entered in the search box", function () {

        $scope.selectedColour = $scope.colours[0];

        // Set our view html.
        var html = '<select class="ac-select" ac-model="selectedColour" ac-options="selectedColour.name for colour in colours"></select>';
        var element = compileHTML(html);
        
        var ul = element.find("UL");
        expect(ul.length).toEqual(1);
        var items = element.find("LI");
        expect(items.length).toEqual(5);

        var dropdownDiv = element.find(".ac-select-popup");
        expect(dropdownDiv.length).toEqual(1);
        var searchBox = dropdownDiv.find("INPUT");
        expect(searchBox.length).toEqual(1);
        sendKey("r", searchBox);

        $timeout(function () {
            sendKey(13, searchBox);
            expect(typeof $scope.selectedColour).toBe("object");
            expect($scope.selectedColour.name).toBe("red");

            $timeout(function () {
                // Delete should clear the selection
                sendKey(keyCodes.del, searchBox);
                expect($scope.selectedColour).toBe(null);
            }, 500);

        }, 500);

    });

    it("Correctly updates the object specified by ac-model when the directive is used within an ng-switch directive.", function () {

        $scope.selectedColour = $scope.colours[2]; // red
        $scope.selectType = "basic";

        // Set our view html.
        var html =
        '<div ng-switch="selectType">' +
            '<div ng-switch-when="basic">' +
                '<select class="ac-select" ac-model="selectedColour" ac-options="selectedColour.name for colour in colours"></select>' +
            '</div>' +
        '</div>';

        var element = compileHTML(html);
        var dropdownDiv = element.find(".ac-select-popup");
        var searchBox = dropdownDiv.find("INPUT");

        sendKey("y", searchBox);

        $timeout(function () {
            sendKey(13, searchBox);
            expect($scope.selectedColour.name).toBe("yellow");
        }, 500);
    });

    it("Displays the text value from the ac-model object when loadOnCreate and loadOnOpen are false.", function () {

        $scope.selectedColour = $scope.colours[0];  // black

        // Set our view html.
        var html = '<select class="ac-select" ac-model="selectedColour"' +
            ' ac-settings="{ loadOnCreate: false, loadOnOpen: false }" ac-options="selectedColour.name for colour in colours"></select>';
        var element = compileHTML(html);

        var displayText = element.find(".ac-select-display").text().trim();
        expect(displayText).toBe("black");

    });



    function compileHTML(html) {
        // Get the jqLite or jQuery element
        var element = angular.element(html);

        // Compile the element into a function to process the view.
        var compiled = $compile(element);

        // Run the compiled view.
        compiled($scope);

        // Call digest on the scope!
        $scope.$digest();

        return element;
    }

    function sendClick(element) {
        var e = $.Event("click");
        element.trigger(e);
    }

    function sendKey(key, element) {
        var keyCode = key;
        if (typeof key === "string") {
            keyCode = key.charCodeAt(0);
        }
        var e = $.Event("keydown", { keyCode: keyCode });
        element.trigger(e);
    }
});

