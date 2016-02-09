"""
    Tests of comprehensive themes. Tests include the following scenarios

     1. test that html overrides are applied from the enabled theme.
     2. test Static files finder and storage settings with or without a theme.
     3. test logo image overrides from enabled theme
     4. test css overrides from enabled theme
     5. test that sass compilation order does not affect sass override behavior
"""

from django.conf import settings
from django.test import TestCase
from django.contrib import staticfiles

from mock import patch
from paver.easy import call_task

from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme

from pavelib import assets


class TestComprehensiveThemes(TestCase):
    """
        Test comprehensive Themes. Tests include static files, html, sass overrides tests.
    """

    def setUp(self):
        """
            Perform setup operations common to all test cases.
        """
        super(TestComprehensiveThemes, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
            Perform setup operations common to all test cases but the operations should be performed
            only once during the tests.
        """
        # first compile lms sass
        # Compile sass for lms
        call_task('pavelib.assets.compile_sass')

        # Apply Comprehensive theme and compile sass assets.
        with patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': settings.TEST_THEME}):
            # Configure path for themes
            assets.configure_paths()
            call_task('pavelib.assets.compile_sass')

        super(TestComprehensiveThemes, cls).setUpClass()

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_green_footer(self):
        """
        Test that lms/footer.html is used from comprehensive theme.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # This string comes from header.html of test-theme
        self.assertContains(resp, "This is a footer for test-theme.")

    def test_theme_adjusts_staticfiles_search_path(self):
        """
        Test that static files finders are adjusted according to the applied comprehensive theme.
        """
        # Test that a theme adds itself to the staticfiles search path.
        before_finders = list(settings.STATICFILES_FINDERS)
        before_dirs = list(settings.STATICFILES_DIRS)

        @with_comprehensive_theme(settings.TEST_THEME)
        def do_the_test(self):
            """A function to do the work so we can use the decorator."""
            self.assertEqual(list(settings.STATICFILES_FINDERS), before_finders)
            self.assertEqual(settings.STATICFILES_DIRS[0], settings.TEST_THEME / 'lms/static')
            self.assertEqual(settings.STATICFILES_DIRS[1:], before_dirs)

        do_the_test(self)

    def test_default_logo_image(self):
        """
        Test that default logo is picked in case of no comprehensive theme.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.REPO_ROOT / 'lms/static/images/logo.png')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_overridden_logo_image(self):
        """
        Test that logo is picked from the applied comprehensive theme.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.TEST_THEME / 'lms/static/images/logo.png')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_overridden_css_files(self):
        """
        Test that css files are overridden according to sass overrides applied by the comprehensive theme.
        """
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.TEST_THEME / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertIn("background:#00fa00", lms_main_css)

    def test_default_css_files(self):
        """
        Test that default css files served without comprehensive themes applied.
        """
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.REPO_ROOT / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", lms_main_css)


class TestComprehensiveThemeReversedSassCompilation(TestCase):
    """
        Test Sass compilation order and sass overrides for comprehensive themes.
    """

    def setUp(self):
        """
            Perform setup operations common to all test cases.
        """
        super(TestComprehensiveThemeReversedSassCompilation, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
            Perform setup operations common to all test cases but the operations should be performed
            only once during the tests.
        """
        # first compile theme sass
        # Apply Comprehensive theme and compile sass assets.
        with patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': settings.TEST_THEME}):
            # Configure path for themes
            assets.configure_paths()
            call_task('pavelib.assets.compile_sass')

        # Compile sass for lms
        call_task('pavelib.assets.compile_sass')
        super(TestComprehensiveThemeReversedSassCompilation, cls).setUpClass()

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_overridden_css_files(self):
        """
        Test that css files are overridden according to sass overrides applied by the comprehensive theme.
        """
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.TEST_THEME / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertIn("background:#00fa00", lms_main_css)

    def test_default_css_files(self):
        """
        Test that default css files served without comprehensive themes applied.
        """
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.REPO_ROOT / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", lms_main_css)
