from django.core.management.base import BaseCommand
from optparse import make_option
import sys
import os

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--failfast', action='store_true', dest='failfast', default=False,
            help='Tells Django to stop running the test suite after first failed test.'),
        make_option('--profile', action='store_true', dest='profile',
            help='Enable profiling. Write profiles into system\'s temporary directory'),
        make_option('--profdir', dest='profile_temp_dir', default=None,
            help='Specifies the directory in which to store profile data.'),
    )
    help = 'Runs the test suite for the specified applications, or the entire site if no apps are specified.'
    args = '[appname ...]'

    requires_model_validation = False

    def handle(self, *test_labels, **options):
        from django.conf import settings
        from django.test.utils import get_runner

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive', True)
        failfast = options.get('failfast', False)
        profile = options.get('profile', False)
        profile_temp_dir = options.get('profile_temp_dir', None)
        TestRunner = get_runner(settings)
      
        def regularHandler():
            if hasattr(TestRunner, 'func_name'):
                # Pre 1.2 test runners were just functions,
                # and did not support the 'failfast' option.
                import warnings
                warnings.warn(
                    'Function-based test runners are deprecated. Test runners should be classes with a run_tests() method.',
                    DeprecationWarning
                )
                failures = TestRunner(test_labels, verbosity=verbosity, interactive=interactive)
            else:
                test_runner = TestRunner(verbosity=verbosity, interactive=interactive, failfast=failfast)
                failures = test_runner.run_tests(test_labels)
    
            if failures:
                sys.exit(bool(failures))

        if profile:
            import cProfile, time, tempfile
            if profile_temp_dir is not None:
                tempfile.tempdir = profile_temp_dir
            def make_profiler_handler(inner_handler):
                def handler(*args, **kwargs):
                    prefix = 'p.%3f' % time.time()
                    fd, profname = tempfile.mkstemp('.prof', prefix)
                    os.close(fd)
                    prof = cProfile.Profile() 
                    try:
                        return prof.runcall(inner_handler, *args, **kwargs)
                    finally:
                        prof.dump_stats(profname)
                return handler
            return make_profiler_handler(regularHandler)()
        else:
            return regularHandler()
        