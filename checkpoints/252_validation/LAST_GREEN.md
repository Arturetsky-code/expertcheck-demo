# ExpertCheck 25.2 branch validation

Validated source commit: 

Successful checks:

- EEEEEEEEEEEEEEEEEEEEEEE                                                  [100%]
==================================== ERRORS ====================================
____ ERROR at setup of test_negative_applicability_can_close_through_core25 ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d7740>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_factual_normative_assertion_can_close_but_reference_only_cannot _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d56c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_site_presence_scope_is_not_forced_to_unbound ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d51c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_unverified_candidate_never_becomes_core25_proof ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d5940>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_unresolved_negative_requirement_is_safe_project_global_and_closes _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d58a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d5c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_admission_diagnostics_distinguish_unverified_candidate _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d7ec0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d5800>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_short_presence_requirement_can_be_verified_when_all_terms_match _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d7560>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_support_wall_requirement_is_not_misbound_to_loader_or_dsk _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c9a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_modular_building_and_canopy_requirements_get_profile_sections _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c4a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_contractual_handover_materials_are_not_assignment_design_requirements _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c900>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___ ERROR at setup of test_negative_applicability_requires_same_local_clause ___

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d7ec0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_construction_duration_design_determined_requires_actual_duration_value _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c87ade0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core25_design_determined_structured_duration_can_close _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d5260>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_secondary_determine_clause_does_not_reclassify_primary_presence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c8d7ec0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_requires_all_conditions _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c9a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_scope_precedes_inherited_dsk_equipment_owner _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79ccc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_accumulates_realistic_split_page_evidence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79d1c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_reaches_core25_verified_ok _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c680>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_lighting_composite_requires_all_five_conditions ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c5e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lighting_composite_reaches_core25_only_after_full_gate _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79d120>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_electrical_lighting_routes_to_system_scope _______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7f0a4c79c720>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7f0a606500e0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
=========================== short test summary info ============================
ERROR tests/core25/test_coverage_breakthrough_252.py::test_negative_applicability_can_close_through_core25 - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_factual_normative_assertion_can_close_but_reference_only_cannot - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_site_presence_scope_is_not_forced_to_unbound - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_unverified_candidate_never_becomes_core25_proof - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_unresolved_negative_requirement_is_safe_project_global_and_closes - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_admission_diagnostics_distinguish_unverified_candidate - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_short_presence_requirement_can_be_verified_when_all_terms_match - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_support_wall_requirement_is_not_misbound_to_loader_or_dsk - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_modular_building_and_canopy_requirements_get_profile_sections - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_contractual_handover_materials_are_not_assignment_design_requirements - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_negative_applicability_requires_same_local_clause - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_construction_duration_design_determined_requires_actual_duration_value - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_core25_design_determined_structured_duration_can_close - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_secondary_determine_clause_does_not_reclassify_primary_presence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_requires_all_conditions - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_scope_precedes_inherited_dsk_equipment_owner - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_accumulates_realistic_split_page_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_reaches_core25_verified_ok - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lighting_composite_requires_all_five_conditions - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lighting_composite_reaches_core25_only_after_full_gate - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_electrical_lighting_routes_to_system_scope - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
23 errors in 1.19s
- EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE [ 72%]
EEEEEEEEEEEEEEEEEEEEEEEEEEE                                              [100%]
==================================== ERRORS ====================================
________ ERROR at setup of test_wrong_owner_cannot_bind_same_parameter _________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b57d80>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_correct_structured_owner_and_parameter_bind ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b57a60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_matching_owner_with_wrong_parameter_is_rejected ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91300>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_project_global_value_can_bind_without_owner ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b905e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_object_specific_semantic_alias_without_structured_owner_is_ambiguous _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b90f40>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_noncanonical_evidence_is_not_proof_eligible ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b919e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____________ ERROR at setup of test_categorical_states_are_explicit ____________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91b20>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__ ERROR at setup of test_compliant_requires_concrete_proof_not_only_proof_id __

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1580>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_noncompliant_requires_concrete_proof_not_only_proof_id _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91da0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_categorical_trace_rejects_binding_for_different_evidence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91f80>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_proof_eligible_blocks_toc_source_kind_even_with_benign_source_role _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b925c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_decision_rejects_conflicting_explicit_proof_id _____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b922a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_categorical_trace_requires_bound_binding_for_every_proof_evidence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1940>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___ ERROR at setup of test_categorical_trace_rejects_requirement_id_mismatch ___

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1bc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core20_assignment_requirement_preserves_route_and_scope _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92ac0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
________ ERROR at setup of test_core20_evidence_keeps_canonical_address ________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91d00>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_raw_assignment_requirement_normalizes_to_same_contract _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92340>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core20_topic_alignment_keeps_stable_baseline_contract _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92ca0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_negative_applicability_can_close_through_core25 ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b90400>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_factual_normative_assertion_can_close_but_reference_only_cannot _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92fc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_site_presence_scope_is_not_forced_to_unbound ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_unverified_candidate_never_becomes_core25_proof ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91300>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_unresolved_negative_requirement_is_safe_project_global_and_closes _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b93420>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_admission_diagnostics_distinguish_unverified_candidate _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b91c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92a20>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_short_presence_requirement_can_be_verified_when_all_terms_match _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b936a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_support_wall_requirement_is_not_misbound_to_loader_or_dsk _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b93ce0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_modular_building_and_canopy_requirements_get_profile_sections _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b932e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_contractual_handover_materials_are_not_assignment_design_requirements _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92b60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___ ERROR at setup of test_negative_applicability_requires_same_local_clause ___

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b93920>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_construction_duration_design_determined_requires_actual_duration_value _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b932e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core25_design_determined_structured_duration_can_close _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92b60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_secondary_determine_clause_does_not_reclassify_primary_presence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b93ba0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_requires_all_conditions _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b936a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_scope_precedes_inherited_dsk_equipment_owner _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92ac0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_accumulates_realistic_split_page_evidence _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1580>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lightning_grounding_composite_reaches_core25_verified_ok _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b92b60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_lighting_composite_requires_all_five_conditions ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1580>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_lighting_composite_reaches_core25_only_after_full_gate _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660040>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_electrical_lighting_routes_to_system_scope _______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660860>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_table_of_contents_entry_is_rejected_even_when_addressable _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660040>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____________ ERROR at setup of test_real_page_fragment_is_canonical ____________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06604a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
________ ERROR at setup of test_unaddressable_semantic_hit_is_rejected _________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660040>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___________ ERROR at setup of test_heading_only_metadata_is_rejected ___________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660360>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_qualify_evidence_filters_section_and_orders_structured_first _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660cc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__________ ERROR at setup of test_test78_golden_case[toc_as_evidence] __________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b54040>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
________ ERROR at setup of test_test78_golden_case[wrong_object_owner] _________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661300>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_test78_golden_case[wrong_semantic_parameter] ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06609a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_______ ERROR at setup of test_test78_golden_case[owner_section_absent] ________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660900>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_test78_golden_case[judge_critic_without_canonical_proof] _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0b93380>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_test78_golden_case[provider_429_not_success] ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0cf1580>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
________ ERROR at setup of test_test78_golden_case[nan_value_rejected] _________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661300>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__ ERROR at setup of test_test78_golden_case[canonical_proof_trace_required] ___

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661080>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_test78_golden_case[positive_semantic_without_selected_evidence] _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661bc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__ ERROR at setup of test_categorical_decision_requires_addressable_evidence ___

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661d00>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_categorical_decision_requires_proven_binding_when_owner_required _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661760>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____________ ERROR at setup of test_review_is_allowed_without_proof ____________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662020>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_persistence_roundtrip_preserves_canonical_trace ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06609a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_plural_persistence_roundtrip_preserves_order_and_trace _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661800>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
______ ERROR at setup of test_report_trace_row_is_auditable_and_sanitized ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06609a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_______ ERROR at setup of test_report_row_matches_public_task9_contract ________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662160>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_report_row_fails_closed_for_invalid_categorical_trace _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06609a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___ ERROR at setup of test_report_trace_row_pairs_binding_with_its_evidence ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660cc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_report_row_rejects_forged_cross_owner_categorical_result _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06627a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_load_results_rejects_tampered_cross_owner_trace ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662c00>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_positive_semantic_judgment_without_selected_evidence_stays_insufficient _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06628e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___________ ERROR at setup of test_bound_typed_value_match_is_proven ___________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663060>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_________ ERROR at setup of test_bound_typed_value_mismatch_is_proven __________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
________ ERROR at setup of test_conflicting_bound_values_require_review ________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06628e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_unbound_value_cannot_create_categorical_proof _____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663060>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_bound_presence_with_project_assertion_is_proven ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06625c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
____ ERROR at setup of test_presence_without_project_assertion_stays_review ____

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662ca0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
___________ ERROR at setup of test_reserve_topology_match_is_proven ____________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06609a0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__________ ERROR at setup of test_reserve_topology_mismatch_is_proven __________

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662f20>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_release_gate_classifies_only_explicit_legacy_diagnostics _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660cc0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_______ ERROR at setup of test_release_gate_never_allows_unknown_failure _______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06637e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_release_gate_separates_baseline_existing_debt_from_new_regressions _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663560>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_release_gate_extracts_pytest_failed_nodeids_without_duplicates _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0662ac0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__ ERROR at setup of test_project_global_numeric_route_does_not_require_owner __

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663560>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_____ ERROR at setup of test_object_specific_numeric_route_requires_owner ______

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06639c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
__ ERROR at setup of test_table_cell_value_keeps_structured_source_preference __

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663560>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_unsupported_semantic_requirement_routes_to_review_kind _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0660720>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_runtime_bridge_promotes_verified_directed_value_through_core25 _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661760>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_runtime_bridge_does_not_promote_candidate_without_proven_owner_match _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663920>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_runtime_bridge_routes_unsupported_requirement_to_review _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663f60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_public_assignment_payload_prefers_core25_and_never_silently_falls_back_on_runtime_error _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663ec0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_legacy_snapshot_without_core25_payload_remains_readable _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8040>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core25_categorical_assignment_verdict_is_not_redowngraded_by_legacy_gate _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663f60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_core25_categorical_assignment_verdict_still_fails_closed_without_trace _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0661c60>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_ai_ledger_prunes_phantom_checkpoint_responses_and_uses_current_rows _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06639c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_review_question_cannot_be_promoted_to_high_risk_by_knowledge_scenario _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb0663ba0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_report_summary_separates_incomplete_set_from_user_confirmation _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb06628e0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_real_pipeline_invokes_core25_runtime_bridge_and_persists_public_payload _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8c20>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_streamlit_build_identifies_25_alpha1_and_assignment_surfaces_use_core25_selector _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8a40>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_studio_context_declares_workspace_store_and_all_constructors_supply_it _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8e00>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_autosave_uses_workspace_store_save_project_contract_explicitly _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8b80>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_fresh_project_routes_to_upload_before_dataframe_empty_access _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d87c0>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
_ ERROR at setup of test_project_page_runtime_contract_is_satisfied_by_studio_context _

name = '__init__', package = None

    def import_module(name, package=None):
        """Import a module.
    
        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.
    
        """
        level = 0
        if name.startswith('.'):
            if not package:
                raise TypeError("the 'package' argument is required to perform a "
                                f"relative import for {name!r}")
            for character in name:
                if character != '.':
                    break
                level += 1
>       return _bootstrap._gcd_import(name[level:], package, level)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

/usr/lib/python3.12/importlib/__init__.py:90: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    """ExpertCheck Core 2.0: universal, knowledge-driven analysis services."""
>   from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package

__init__.py:2: ImportError

The above exception was the direct cause of the following exception:

cls = <class '_pytest.runner.CallInfo'>
func = <function call_and_report.<locals>.<lambda> at 0x7fbfb03d8b80>
when = 'setup'
reraise = (<class '_pytest.outcomes.Exit'>, <class 'KeyboardInterrupt'>)

    @classmethod
    def from_call(
        cls,
        func: Callable[[], TResult],
        when: Literal["collect", "setup", "call", "teardown"],
        reraise: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    ) -> CallInfo[TResult]:
        """Call func, wrapping the result in a CallInfo.
    
        :param func:
            The function to call. Called without arguments.
        :type func: Callable[[], _pytest.runner.TResult]
        :param when:
            The phase in which the function is called.
        :param reraise:
            Exception or exceptions that shall propagate if raised by the
            function, instead of being wrapped in the CallInfo.
        """
        excinfo = None
        instant = timing.Instant()
        try:
>           result: TResult | None = func()
                                     ^^^^^^

../../../.local/lib/python3.12/site-packages/_pytest/runner.py:361: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:250: in <lambda>
    lambda: runtest_hook(item=item, **kwds),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_hooks.py:512: in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/pluggy/_manager.py:120: in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/logging.py:858: in pytest_runtest_setup
    yield
../../../.local/lib/python3.12/site-packages/_pytest/capture.py:895: in pytest_runtest_setup
    return (yield)
            ^^^^^
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:170: in pytest_runtest_setup
    item.session._setupstate.setup(item)
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:529: in setup
    raise exc[0].with_traceback(exc[1])
../../../.local/lib/python3.12/site-packages/_pytest/runner.py:536: in setup
    col.setup()
../../../.local/lib/python3.12/site-packages/_pytest/python.py:678: in setup
    init_mod = importtestmodule(self.path / "__init__.py", self.config)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

path = PosixPath('/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py')
config = <_pytest.config.Config object at 0x7fbfc4ad08c0>

    def importtestmodule(
        path: Path,
        config: Config,
    ):
        # We assume we are only called once per module.
        importmode = config.getoption("--import-mode")
        try:
            mod = import_path(
                path,
                mode=importmode,
                root=config.rootpath,
                consider_namespace_packages=config.getini("consider_namespace_packages"),
            )
        except SyntaxError as e:
            raise nodes.Collector.CollectError(
                ExceptionInfo.from_current().getrepr(style="short")
            ) from e
        except ImportPathMismatchError as e:
            raise nodes.Collector.CollectError(
                "import file mismatch:\n"
                "imported module {!r} has this __file__ attribute:\n"
                "  {}\n"
                "which is not the same as the test file we want to collect:\n"
                "  {}\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules".format(*e.args)
            ) from e
        except ImportError as e:
            exc_info = ExceptionInfo.from_current()
            if config.get_verbosity() < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = (
                exc_info.getrepr(style="short")
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
>           raise nodes.Collector.CollectError(
                f"ImportError while importing test module '{path}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                f"{formatted_tb}"
            ) from e
E           _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
E           Hint: make sure your test modules/packages have valid Python names.
E           Traceback:
E           /usr/lib/python3.12/importlib/__init__.py:90: in import_module
E               return _bootstrap._gcd_import(name[level:], package, level)
E                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           __init__.py:2: in <module>
E               from .pipeline import analyze_uploaded_core
E           E   ImportError: attempted relative import with no known parent package

../../../.local/lib/python3.12/site-packages/_pytest/python.py:538: CollectError
=========================== short test summary info ============================
ERROR tests/core25/test_binding.py::test_wrong_owner_cannot_bind_same_parameter - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_binding.py::test_correct_structured_owner_and_parameter_bind - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_binding.py::test_matching_owner_with_wrong_parameter_is_rejected - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_binding.py::test_project_global_value_can_bind_without_owner - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_binding.py::test_object_specific_semantic_alias_without_structured_owner_is_ambiguous - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_noncanonical_evidence_is_not_proof_eligible - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_categorical_states_are_explicit - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_compliant_requires_concrete_proof_not_only_proof_id - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_noncompliant_requires_concrete_proof_not_only_proof_id - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_categorical_trace_rejects_binding_for_different_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_proof_eligible_blocks_toc_source_kind_even_with_benign_source_role - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_decision_rejects_conflicting_explicit_proof_id - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_categorical_trace_requires_bound_binding_for_every_proof_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_contracts.py::test_categorical_trace_rejects_requirement_id_mismatch - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_core20_adapter.py::test_core20_assignment_requirement_preserves_route_and_scope - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_core20_adapter.py::test_core20_evidence_keeps_canonical_address - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_core20_adapter.py::test_raw_assignment_requirement_normalizes_to_same_contract - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_core20_adapter.py::test_core20_topic_alignment_keeps_stable_baseline_contract - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_negative_applicability_can_close_through_core25 - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_factual_normative_assertion_can_close_but_reference_only_cannot - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_site_presence_scope_is_not_forced_to_unbound - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_unverified_candidate_never_becomes_core25_proof - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_unresolved_negative_requirement_is_safe_project_global_and_closes - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_admission_diagnostics_distinguish_unverified_candidate - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_short_presence_requirement_can_be_verified_when_all_terms_match - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_support_wall_requirement_is_not_misbound_to_loader_or_dsk - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_modular_building_and_canopy_requirements_get_profile_sections - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_contractual_handover_materials_are_not_assignment_design_requirements - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_negative_applicability_requires_same_local_clause - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_construction_duration_design_determined_requires_actual_duration_value - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_core25_design_determined_structured_duration_can_close - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_secondary_determine_clause_does_not_reclassify_primary_presence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_requires_all_conditions - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_scope_precedes_inherited_dsk_equipment_owner - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_accumulates_realistic_split_page_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lightning_grounding_composite_reaches_core25_verified_ok - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lighting_composite_requires_all_five_conditions - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_lighting_composite_reaches_core25_only_after_full_gate - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_coverage_breakthrough_252.py::test_electrical_lighting_routes_to_system_scope - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_evidence_gate.py::test_table_of_contents_entry_is_rejected_even_when_addressable - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_evidence_gate.py::test_real_page_fragment_is_canonical - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_evidence_gate.py::test_unaddressable_semantic_hit_is_rejected - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_evidence_gate.py::test_heading_only_metadata_is_rejected - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_evidence_gate.py::test_qualify_evidence_filters_section_and_orders_structured_first - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[toc_as_evidence] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[wrong_object_owner] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[wrong_semantic_parameter] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[owner_section_absent] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[judge_critic_without_canonical_proof] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[provider_429_not_success] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[nan_value_rejected] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[canonical_proof_trace_required] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_golden_test78.py::test_test78_golden_case[positive_semantic_without_selected_evidence] - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_integrity_gate.py::test_categorical_decision_requires_addressable_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_integrity_gate.py::test_categorical_decision_requires_proven_binding_when_owner_required - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_integrity_gate.py::test_review_is_allowed_without_proof - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_persistence_roundtrip_preserves_canonical_trace - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_plural_persistence_roundtrip_preserves_order_and_trace - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_report_trace_row_is_auditable_and_sanitized - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_report_row_matches_public_task9_contract - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_report_row_fails_closed_for_invalid_categorical_trace - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_report_trace_row_pairs_binding_with_its_evidence - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_report_row_rejects_forged_cross_owner_categorical_result - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_persistence_report_trace.py::test_load_results_rejects_tampered_cross_owner_trace - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_positive_semantic_judgment_without_selected_evidence_stays_insufficient - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_bound_typed_value_match_is_proven - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_bound_typed_value_mismatch_is_proven - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_conflicting_bound_values_require_review - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_unbound_value_cannot_create_categorical_proof - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_bound_presence_with_project_assertion_is_proven - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_presence_without_project_assertion_stays_review - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_reserve_topology_match_is_proven - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_proof_decision.py::test_reserve_topology_mismatch_is_proven - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_release_gate_classification.py::test_release_gate_classifies_only_explicit_legacy_diagnostics - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_release_gate_classification.py::test_release_gate_never_allows_unknown_failure - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_release_gate_classification.py::test_release_gate_separates_baseline_existing_debt_from_new_regressions - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_release_gate_classification.py::test_release_gate_extracts_pytest_failed_nodeids_without_duplicates - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_requirement_routing.py::test_project_global_numeric_route_does_not_require_owner - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_requirement_routing.py::test_object_specific_numeric_route_requires_owner - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_requirement_routing.py::test_table_cell_value_keeps_structured_source_preference - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_requirement_routing.py::test_unsupported_semantic_requirement_routes_to_review_kind - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_bridge.py::test_runtime_bridge_promotes_verified_directed_value_through_core25 - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_bridge.py::test_runtime_bridge_does_not_promote_candidate_without_proven_owner_match - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_bridge.py::test_runtime_bridge_routes_unsupported_requirement_to_review - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_bridge.py::test_public_assignment_payload_prefers_core25_and_never_silently_falls_back_on_runtime_error - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_bridge.py::test_legacy_snapshot_without_core25_payload_remains_readable - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_integrity_251.py::test_core25_categorical_assignment_verdict_is_not_redowngraded_by_legacy_gate - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_integrity_251.py::test_core25_categorical_assignment_verdict_still_fails_closed_without_trace - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_integrity_251.py::test_ai_ledger_prunes_phantom_checkpoint_responses_and_uses_current_rows - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_integrity_251.py::test_review_question_cannot_be_promoted_to_high_risk_by_knowledge_scenario - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_integrity_251.py::test_report_summary_separates_incomplete_set_from_user_confirmation - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_wiring.py::test_real_pipeline_invokes_core25_runtime_bridge_and_persists_public_payload - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_runtime_wiring.py::test_streamlit_build_identifies_25_alpha1_and_assignment_surfaces_use_core25_selector - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_workspace_runtime_integration.py::test_studio_context_declares_workspace_store_and_all_constructors_supply_it - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_workspace_runtime_integration.py::test_autosave_uses_workspace_store_save_project_contract_explicitly - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_workspace_runtime_integration.py::test_fresh_project_routes_to_upload_before_dataframe_empty_access - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
ERROR tests/core25/test_workspace_runtime_integration.py::test_project_page_runtime_contract_is_satisfied_by_studio_context - _pytest.nodes.Collector.CollectError: ImportError while importing test module '/home/runner/work/expertcheck-demo/expertcheck-demo/__init__.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
__init__.py:2: in <module>
    from .pipeline import analyze_uploaded_core
E   ImportError: attempted relative import with no known parent package
99 errors in 4.27s
