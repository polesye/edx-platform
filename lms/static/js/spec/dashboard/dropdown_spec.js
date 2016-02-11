define(['jquery.simulate', 'js/dashboard/dropdown'],
    function(TemplateHelpers, AjaxHelpers) {
        'use strict';

        describe("edx.dashboard.dropdown.toggleCourseActionsDropdownMenu", function() {

            beforeEach(function() {
                loadFixtures('js/fixtures/dashboard/dashboard.html');
                edx.dashboard.dropdown.bindToggleButtons();
            });

            var keys = $.simulate.keyCode,
                toggleButtonSelector = '#actions-dropdown-link-2',
                dropdownSelector = '#actions-dropdown-2',
                dropdownItemSelector = '#actions-dropdown-2 li a',
                clickToggleButton = function() {
                    $(toggleButtonSelector).click();
                },
                verifyDropdownVisible = function() {
                    expect($(dropdownSelector)).toBeVisible();
                },
                verifyDropdownNotVisible = function() {
                    expect($(dropdownSelector)).not.toBeVisible();
                },
                openDropDownMenu = function() {
                    verifyDropdownNotVisible();
                    clickToggleButton();
                    verifyDropdownVisible();
                },
                keydown = function(keyInfo) {
                    $(document.activeElement).simulate("keydown", keyInfo);
                };

            it("Clicking the .action-more button toggles the menu", function() {
                verifyDropdownNotVisible();
                clickToggleButton();
                verifyDropdownVisible();
                clickToggleButton();
                verifyDropdownNotVisible();
            });
            it("When the dropdown is opened focus is trapped (tab key)", function() {
                openDropDownMenu();
                expect($(dropdownItemSelector).first()).toBeFocused();
                keydown({ keyCode: keys.TAB, shiftKey: true });
                expect($(dropdownItemSelector).last()).toBeFocused();
                keydown({ keyCode: keys.TAB });
                expect($(dropdownItemSelector).first()).toBeFocused();
            });
            it("When the dropdown is opened focus is trapped (arrow keys)", function() {
                openDropDownMenu();
                expect($(dropdownItemSelector).first()).toBeFocused();
                keydown({ keyCode: keys.UP });
                expect($(dropdownItemSelector).last()).toBeFocused();
                keydown({ keyCode: keys.DOWN });
                expect($(dropdownItemSelector).first()).toBeFocused();
            });
            it("ESCAPE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.ESCAPE });
                verifyDropdownNotVisible();
                expect($(toggleButtonSelector)).toBeFocused();
            });
            it("SPACE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.SPACE });
                verifyDropdownNotVisible();
                expect($(toggleButtonSelector)).toBeFocused();
            });
        });
    }
);
