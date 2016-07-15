from hitchtest import HitchPackage, utils
from subprocess import check_output, call
from hitchtest.environment import checks
from os import makedirs, chdir, chmod
from os.path import join, exists
import shutil
import getpass
import hitchmysql
import stat
import os


# libncurses5-dev
ISSUES_URL = "http://github.com/hitchtest/hitchmysql/issues"

MYCNF = """[mysqld]
user={1}
basedir={0}
port=13307
max_allowed_packet=64M
wait_timeout=6000

[mysqld_safe]
lc-messages-dir={0}

[client]
port=13307
user={1}

[mysqladmin]
user=root
port=13307

[mysql]
port=13307

[mysql_install_db]
user={1}
port=3307
basedir={0}
datadir={0}/data
mpdir=/tmp/"""


class MySQLPackage(HitchPackage):
    VERSIONS = [
        "5.7.7 rc", "5.7.6 m16", "5.7.5 m15", "5.7.4 m14", "5.7.3 m13", "5.7.2 m12", "5.7.1 m11",
        "5.6.26", "5.6.25", "5.6.24", "5.6.23", "5.6.22", "5.6.21",
        "5.6.20", "5.6.19", "5.6.17", "5.6.16", "5.6.15", "5.6.14", "5.6.13", "5.6.12", "5.6.11", "5.6.10",
        "5.6.9 rc", "5.6.8 rc", "5.6.7 rc", "5.6.6 m9", "5.6.5 m8", "5.6.4 m7", "5.6.3 m6", "5.6.2 m5",
        "5.5.44", "5.5.43", "5.5.42", "5.5.41", "5.5.40",
        "5.5.39", "5.5.38", "5.5.37", "5.5.36", "5.5.35",
        "5.5.34", "5.5.33", "5.5.32", "5.5.31", "5.5.30", "5.5.29", "5.5.28", "5.5.27",
        "5.5.25a", "5.5.24", "5.5.23", "5.5.22", "5.5.21", "5.5.20",
        "5.5.19", "5.5.18", "5.5.17", "5.5.16", "5.5.15", "5.5.14", "5.5.13", "5.5.12", "5.5.11", "5.5.10",
        "5.5.9", "5.5.8", "5.5.7 rc", "5.5.6 rc",
        "5.5.5 m3", "5.5.3 m3", "5.5.4 m3", "5.5.2 m2", "5.5.1 m2", "5.5.0 m2",
        "5.1.72", "5.1.71", "5.1.70",
        "5.1.69", "5.1.68", "5.1.67", "5.1.66", "5.1.65", "5.1.63", "5.1.62", "5.1.61", "5.1.60",
        "5.1.59", "5.1.58", "5.1.57", "5.1.56", "5.1.55", "5.1.54", "5.1.53", "5.1.52", "5.1.51", "5.1.50",
        "5.1.49", "5.1.48", "5.1.47", "5.1.46", "5.1.45", "5.1.44", "5.1.43", "5.1.42", "5.1.41", "5.1.40",
        "5.1.39", "5.1.38", "5.1.37", "5.1.36", "5.1.35", "5.1.34", "5.1.33", "5.1.32", "5.1.31", "5.1.30",
        "5.1.5a alpha", "5.0.96", "5.0.95", "5.0.92", "5.0.91", "5.0.90",
        "5.0.89", "5.0.88", "5.0.87", "5.0.86", "5.0.85", "5.0.84", "5.0.83", "5.0.82", "5.0.81",
        "5.0.77", "5.0.75", "5.0.67", "5.0.51b", "5.0.51a", "5.0.45b",
        "5.0.45", "5.0.41", "5.0.37", "5.0.33", "5.0.27", "5.0.24a", "5.0.24",
        "5.0.23", "5.0.22", "5.0.21", "5.0.20a", "5.0.20", "5.0.19", "5.0.18",
        "5.0.17a", "5.0.17", "5.0.16a", "5.0.16", "5.0.15a", "5.0.15",
    ]

    name = "MySQL"

    def __init__(self, version, directory=None, bin_directory=None):
        super(MySQLPackage, self).__init__()
        self.version = self.check_version(version, self.VERSIONS, ISSUES_URL)

        if directory is None:
            self.directory = join(self.get_build_directory(), "mysql-{}".format(self.version))
        else:
            self.directory = directory
        self.bin_directory = bin_directory
        checks.packages(hitchmysql.UNIXPACKAGES)

    def verify(self):
        version_output = check_output([self.mysqld, "--version"]).decode('utf8')
        if self.version not in version_output:
            raise RuntimeError("MySQL version needed is {}, output is: {}.".format(self.version, version_output))

    def build(self):
        download_to = join(self.get_downloads_directory(), "mysql-{}.tar.gz".format(self.version))
        download_url = "https://dev.mysql.com/get/Downloads/MySQL-{0}/mysql-{1}.tar.gz".format(
            ".".join(self.version.split(".")[:2]),
            self.version,
        )
        utils.download_file(download_to, download_url)
        if not exists(self.directory):
            utils.extract_archive(download_to, self.get_build_directory())
            chdir(self.directory)
            call(["./BUILD/compile-dist"])
            call([
                "./configure",
                "--prefix={}".format(self.directory),
                "--enable-assembler",
                "--with-mysqld-ldflags=-all-static",
                "--with-client-ldflags=-all-static",
                "--with-mysqld-user={}".format(getpass.getuser()),
                "--with-unix-socket-path={}/tmp/mysql.sock".format(self.directory),
                "--localstatedir={}/data".format(self.directory),
            ])
            call(["make"])
            call(["make", "install"])

            makedirs("tmp")

            st = os.stat('scripts/mysql_install_db.sh')
            chmod('scripts/mysql_install_db.sh', st.st_mode | stat.S_IEXEC)

            st = os.stat('scripts/mysql_install_db')
            chmod('scripts/mysql_install_db', st.st_mode | stat.S_IEXEC)

            shutil.copyfile('scripts/mysql_install_db.sh', 'bin/mysql_install_db.sh')
            st = os.stat('bin/mysql_install_db.sh')
            chmod('bin/mysql_install_db.sh', st.st_mode | stat.S_IEXEC)

            shutil.copyfile('scripts/mysql_install_db', 'bin/mysql_install_db')
            st = os.stat('bin/mysql_install_db')
            chmod('bin/mysql_install_db', st.st_mode | stat.S_IEXEC)

            with open("my.cnf", "w") as mycnf_handle:
                mycnf_handle.write(MYCNF.format(self.directory, getpass.getuser()))
        self.bin_directory = join(self.directory, "bin")

    @property
    def mysqld(self):
        if self.bin_directory is None:
            raise RuntimeError("bin_directory not set.")
        return join(self.bin_directory, "mysqld")

    @property
    def mysql(self):
        if self.bin_directory is None:
            raise RuntimeError("bin_directory not set.")
        return join(self.bin_directory, "mysql")

    @property
    def mysql_install_db(self):
        if self.bin_directory is None:
            raise RuntimeError("bin_directory not set.")
        return join(self.bin_directory, "mysql_install_db.sh")
