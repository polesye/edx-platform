define(['js/dashboard/dropdown', 'jquery.simulate'],
    function(edx.dashboard.dropdown) {
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
                waitForElementToBeFocused = function(element) {
                    // This is being used instead of toBeFocused which is flaky
                    waitsFor(
                        return element[0] === document.activeElement,
                        'Waiting for element to have focus',
                        500
                    );
                }
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
                waitForElementToBeFocused($(dropdownItemSelector).first());
                keydown({ keyCode: keys.TAB, shiftKey: true });
                waitForElementToBeFocused$(dropdownItemSelector).last());
                keydown({ keyCode: keys.TAB });
                waitForElementToBeFocused($(dropdownItemSelector).first());
            });
            it("When the dropdown is opened focus is trapped (arrow keys)", function() {
                openDropDownMenu();
                waitForElementToBeFocused($(dropdownItemSelector).first());
                keydown({ keyCode: keys.UP });
                waitForElementToBeFocused($(dropdownItemSelector).last());
                keydown({ keyCode: keys.DOWN });
                waitForElementToBeFocused($(dropdownItemSelector).first());
            });
            it("ESCAPE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.ESCAPE });
                verifyDropdownNotVisible();
                waitForElementToBeFocused($(toggleButtonSelector));
            });
            it("SPACE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.SPACE });
                verifyDropdownNotVisible();
                waitForElementToBeFocused($(toggleButtonSelector));
            });
        });
    }
);
