import os
import sys
import subprocess

import logging
logger = logging.getLogger(__name__)

class ProducerSpawner(object):
    """
    Spawns a producer process using an alternative Python interpreter.

    The alternative interpreter is determined as follows:
      - If 'config_python_executable' is provided, that path is used.
      - Otherwise, it is built as:
          "<user_home>\\AppData\\Local\\anaconda3\\envs\\<env_name>\\python.exe"
        (with env_name defaulting to "p309").

    The producer process is defined in a separate script in the config file (e.g. "producer.py").
    """
    def __init__(self, producer_script, config_python_executable=None, config_python_env_name=None):
        """
        :param producer_script: Path to the producer script.
        :param config_python_executable: If provided, uses this Python executable; otherwise, it is built from config_python_env_name.
        :param config_python_env_name: Name of the Anaconda environment to use if no executable is provided (default: "p309").
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.producer_script = os.path.join(base_dir, producer_script)
        self.python_executable = self.init_python_interpreter(config_python_executable, config_python_env_name)

        # On Windows, hide the terminal window using startupinfo.
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None

        # Spawn the producer process using the alternative interpreter and set cwd so files are created in the expected directory.
        self.process = subprocess.Popen(
            [self.python_executable, self.producer_script],
            startupinfo=startupinfo
        )
        # stdout, stderr = self.process.communicate(timeout=1)  # adjust timeout as needed
        # logger.info("stdout: %s", str(stdout.decode()))
        # logger.info("stderr: %s", str(stderr.decode()))
        logger.info("Spawned producer process with PID: %d", self.process.pid)

    def init_python_interpreter(self, config_python_executable=None, config_python_env_name=None):
        if config_python_env_name is None:
            config_python_env_name = "p309"

        if config_python_executable is None:
            # Build the path using the current user's home directory.
            user_home = os.path.expanduser("~")
            python_executable = os.path.join(
                user_home,
                "AppData", "Local", "anaconda3", "envs", config_python_env_name, "python.exe"
            )
        else:
            python_executable = config_python_executable

        # Ensure the executable exists.
        assert os.path.exists(python_executable), "Python executable not found at: {}".format(python_executable)

        # Verify the interpreter by running it with '--version'.
        proc = subprocess.Popen([python_executable, "--version"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        returncode = proc.returncode

        stdout_str = stdout.decode("utf-8").strip() if stdout else ""
        stderr_str = stderr.decode("utf-8").strip() if stderr else ""

        # Ensure the command ran successfully.
        assert returncode == 0, "Failed to run python at {}. Error: {}".format(python_executable, stderr_str)

        version_info = stdout_str if stdout_str else stderr_str
        logger.info("Alternative Python interpreter version: %s in %s", version_info, python_executable)
        return python_executable

    def close(self):
        """
        Terminates the producer process.
        """
        logger.info("Stopping process")
        if self.process.poll() is None:  # Process is still running.
            self.process.terminate()
            self.process.wait()
            logger.info("Producer process terminated.")

