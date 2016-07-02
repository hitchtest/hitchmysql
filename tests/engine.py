from commandlib import run
import hitchpython
import hitchserve
import hitchtest
import hitchcli
import kaching


class ExecutionEngine(hitchtest.ExecutionEngine):
    """Hitch bootstrap engine tester."""

    def set_up(self):
        self.path.project = self.path.engine.parent
        self.path.state = self.path.engine.parent.joinpath("state")
        self.path.samples = self.path.engine.joinpath("samples")

        if not self.path.state.exists():
            self.path.state.mkdir()

        if self.settings.get("kaching", False):
            kaching.start()

        self.python_package = hitchpython.PythonPackage(
            python_version="3.5.0" #self.preconditions['python_version']
        )
        self.python_package.build()

        self.python = self.python_package.cmd.python
        self.pip = self.python_package.cmd.pip

        self.cli_steps = hitchcli.CommandLineStepLibrary(
            default_timeout=int(self.settings.get("cli_timeout", 720))
        )

        self.cd = self.cli_steps.cd
        self.run = self.cli_steps.run
        self.expect = self.cli_steps.expect
        self.send_control = self.cli_steps.send_control
        self.send_line = self.cli_steps.send_line
        self.exit_with_any_code = self.cli_steps.exit_with_any_code
        self.exit = self.cli_steps.exit
        self.finish = self.cli_steps.finish

        if "files" in self.preconditions:
            self.path.state.rmtree(ignore_errors=True)
            self.path.state.mkdir()
            for filename, contents in self.preconditions['files'].items():
                self.path.state.joinpath(filename).write_text(contents)

        if "state" in self.preconditions:
            self.path.state.rmtree(ignore_errors=True)
            self.path.samples.joinpath(self.preconditions['state'])\
                             .copytree(self.path.state)

        run(self.pip("uninstall", "hitchmysql", "-y").ignore_errors())
        run(self.pip("uninstall", "hitchtest", "-y").ignore_errors())
        run(self.pip("install", ".").in_dir(self.path.project.joinpath("..", "test")))
        run(self.pip("install", ".").in_dir(self.path.project.joinpath("..", "commandlib")))
        run(self.pip("install", ".").in_dir(self.path.project))
        run(self.pip("install", "ipykernel"))
        run(self.pip("install", "pip", "--upgrade"))
        run(self.pip("install", "pygments", "--upgrade"))

        self.services = hitchserve.ServiceBundle(
            self.path.project,
            startup_timeout=8.0,
            shutdown_timeout=1.0
        )

        #self.services['IPython'] = hitchpython.IPythonKernelService(self.python_package)

        #self.services.startup(interactive=False)
        #self.ipython_kernel_filename = self.services['IPython'].wait_and_get_ipykernel_filename()
        #self.ipython_step_library = hitchpython.IPythonStepLibrary()
        #self.ipython_step_library.startup_connection(self.ipython_kernel_filename)

        #self.run_command = self.ipython_step_library.run
        #self.assert_true = self.ipython_step_library.assert_true
        #self.assert_exception = self.ipython_step_library.assert_exception
        #self.shutdown_connection = self.ipython_step_library.shutdown_connection

        #self.run_command("import os")
        #self.run_command("""os.chdir("{}")""".format(self.path.state))

        #if not self.path.state.exists():
            #self.path.state.mkdir()

        #self.run_command("import hitchtest")
        #self.run_command("import hitchpython")
        #self.run_command("from path import Path")

    def run_python(self, args=None):
        self.cd(self.path.state)
        if args is None:
            args = []
        cmd = self.python(args)
        self.run(cmd.arguments[0], cmd.arguments[1:])

    def lint(self, args=None):
        """Lint the source code."""
        run(self.pip("install", "flake8"))
        run(self.python_package.cmd.flake8(*args).in_dir(self.path.project))

    def mkdir(self, directory):
        self.path.state.joinpath(directory).mkdir()

    def move(self, source=None, dest=None):
        self.path.state.joinpath(source).move(dest)

    def pause(self, message=""):
        if hasattr(self, 'services'):
            self.services.start_interactive_mode()
        self.ipython(message=message)
        if hasattr(self, 'services'):
            self.services.stop_interactive_mode()

    def on_failure(self):
        """Stop and IPython."""
        #if self.settings.get("kaching", False):
            #kaching.fail()
        if self.settings.get("pause_on_failure", False):
            self.pause(message=self.stacktrace.to_template())

    def on_success(self):
        """Ka-ching!"""
        #if self.settings.get("kaching", False):
            #kaching.win()
        if self.settings.get("pause_on_success", False):
            self.pause(message="SUCCESS")

    def tear_down(self):
        """Clean out the state directory."""
        if hasattr(self, 'services'):
            self.services.shutdown()
        self.path.state.rmtree(ignore_errors=True)
