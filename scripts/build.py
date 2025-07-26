import argparse
import logging
import platform
import re
import shutil
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()
handler = RichHandler(console=console)
logger = logging.getLogger("build")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class BuildError(Exception): ...


def get_version_from_config() -> str:
    p = Path("mdcx/consts.py")
    if not p.exists():
        raise BuildError(f"版本配置文件不存在: {p}")
    try:
        content = p.read_text(encoding="utf-8")
        match = re.search(r"LOCAL_VERSION\s*=\s*(\d+)", content)
        if match:
            return match.group(1)
        raise BuildError("无法从代码中获取版本号")
    except Exception as e:
        raise BuildError("获取版本号失败") from e


class BuildManager:
    def __init__(self, app_name: str, app_version: str, create_dmg: bool):
        self.app_name = app_name
        self.app_version = app_version
        self.create_dmg = create_dmg
        self.platform = platform.platform()
        self.os = platform.system()
        self.is_mac = self.os == "Darwin"
        self.is_windows = self.os == "Windows"
        self.is_linux = self.os == "Linux"

    def run(self):
        """运行构建流程"""
        try:
            start_time = time.time()
            if not self.app_version:
                self.app_version = get_version_from_config()

            self._check_environment()
            self._cleanup()
            dist = Path("dist")
            if dist.exists():
                logger.info("清理现有的 dist 目录...")
                shutil.rmtree(dist)

            self._generate_spec()
            if self.is_mac:
                self._modify_spec()
            self._build_app()

            if self.create_dmg and self.is_mac:
                self._create_dmg()

            self._cleanup()
            logger.info(f"构建完成. 耗时: {int(time.time() - start_time)}秒")
        except BuildError as e:
            logger.error(f"构建失败: {e}")
            console.print_exception()
            sys.exit(1)
        except Exception as e:
            logger.error(f"意外错误: {e}")
            sys.exit(1)

    def _check_environment(self):
        logger.info("构建环境:")
        logger.info(f"\t操作系统: {self.platform}")
        logger.info(f"\tPython 版本: {sys.version}")
        logger.info(f"\tPython 可执行文件: {sys.executable}")

        logger.info(f"\t应用名称: {self.app_name}")
        logger.info(f"\t应用版本: {self.app_version}")

        logger.info("检查依赖...")
        # 检查 PyInstaller
        r = self._run_command([sys.executable, "-m", "PyInstaller", "-v"], error_msg="PyInstaller 未安装")
        logger.info(f"\tPyInstaller 版本: {r}")

        # 检查 create-dmg
        if self.is_mac and self.create_dmg:
            r = self._run_command(["create-dmg", "--version"])
            if not r:
                logger.warning("create-dmg 未安装, 尝试安装: brew install create-dmg ...")
                self._run_command(["brew", "install", "create-dmg"], error_msg="create-dmg 安装失败")
                r = self._run_command(["create-dmg", "--version"])
            logger.info(f"\tcreate-dmg 版本: {r}")

        logger.info("检查必要文件...")
        required_files = ["main.py", "mdcx", "resources/Img/MDCx.icns", "resources", "libs"]
        for file_path in required_files:
            if not Path(file_path).exists():
                raise BuildError(f"文件检查失败: {file_path}")

    def _generate_spec(self):
        """生成.spec文件"""
        logger.info("生成 .spec 文件...")
        cmd = [
            "pyi-makespec",
            "--name",
            self.app_name,
            "--noupx",
            *(["--osx-bundle-identifier", "com.mdcuniverse.mdcx"] * self.is_mac),
            *(["--onefile"] if not self.is_mac else []),
            "-w",
            "main.py",
            "-p",
            "./mdcx",
            "--add-data",
            "resources:resources",
            "--add-data",
            "libs:.",
            "--icon",
            "resources/Img/MDCx.icns",
            "--hidden-import",
            "_cffi_backend",
            "--collect-all",
            "curl_cffi",
        ]
        self._run_command(cmd, "✅ 生成 .spec 文件", "spec 文件生成失败")

    def _modify_spec(self):
        """修改.spec文件添加版本信息"""
        logger.info("(macOS) 向 .spec 文件添加版本信息...")

        spec_file = Path(f"{self.app_name}.spec")
        if not spec_file.exists():
            raise BuildError("spec 文件不存在")

        try:
            content = spec_file.read_text(encoding="utf-8")

            # 查找bundle_identifier行
            lines = content.splitlines()
            new_lines = []

            for i, line in enumerate(lines, 1):
                new_lines.append(line)
                if "bundle_identifier" in line:
                    # 在下一行添加info_plist
                    indent = len(line) - len(line.lstrip())
                    info_plist = f"{' ' * indent}info_plist={{\n"
                    info_plist += f"{' ' * (indent + 4)}'CFBundleShortVersionString': '{self.app_version}',\n"
                    info_plist += f"{' ' * (indent + 4)}'CFBundleVersion': '{self.app_version}',\n"
                    info_plist += f"{' ' * indent}}},"
                    new_lines.append(info_plist)
                    logger.debug(f"在第 {i + 1} 行添加 info_plist")

            new_content = "\n".join(new_lines)
            spec_file.write_text(new_content, encoding="utf-8")

            logger.info("✅ .spec 文件修改成功，已添加版本信息")

        except Exception as e:
            raise BuildError("spec文件修改失败") from e

    def _build_app(self):
        """构建应用"""
        logger.info("开始构建应用...")
        build_start = time.time()

        cmd = ["pyinstaller", f"{self.app_name}.spec", "-y"]
        self._run_command(cmd, "✅ 应用构建成功", "pyinstaller 构建失败")
        build_duration = time.time() - build_start

        logger.info(f"✅ 应用构建成功! 耗时: {int(build_duration)}秒")

        # 验证构建结果
        if self.is_windows:
            app_path = Path(f"dist/{self.app_name}.exe")
        elif self.is_mac:
            app_path = Path(f"dist/{self.app_name}.app")
        else:
            app_path = Path(f"dist/{self.app_name}")
        if not app_path.exists():
            raise BuildError("构建未生成")
        logger.info(f"✅ 构建产物: {app_path}")
        with suppress(Exception):
            if app_path.is_file():
                app_size = app_path.stat().st_size
                logger.info(f"大小: {app_size / 1024 / 1024:.1f} MB")

    def _create_dmg(self):
        """创建DMG文件"""
        logger.info("(macOS) 创建 DMG 文件...")
        dmg_start = time.time()
        cmd = [
            "create-dmg",
            "--volname",
            self.app_name,
            "--volicon",
            "resources/Img/MDCx.icns",
            "--window-pos",
            "200",
            "120",
            "--window-size",
            "800",
            "400",
            "--icon-size",
            "80",
            "--icon",
            f"{self.app_name}.app",
            "300",
            "36",
            "--hide-extension",
            f"{self.app_name}.app",
            "--app-drop-link",
            "500",
            "36",
            f"dist/{self.app_name}.dmg",
            f"dist/{self.app_name}.app",
        ]
        logger.debug(f"Execute: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        dmg_duration = time.time() - dmg_start

        if result.returncode != 0:
            raise BuildError("DMG 文件创建失败: " + result.stdout.strip())
        logger.debug("DMG 创建输出: ", result.stdout.strip())

        logger.info(f"✅ DMG 文件创建成功! 耗时: {int(dmg_duration)}秒")

        # 验证DMG文件
        dmg_path = Path(f"dist/{self.app_name}.dmg")
        logger.info(f"✅ DMG 文件: {dmg_path}")
        with suppress(Exception):
            dmg_size = dmg_path.stat().st_size
            logger.info(f"大小: {dmg_size >> 20:.1f} MB")

    def _cleanup(self):
        """清理临时文件"""
        logger.info("清理临时文件...")
        # 清理build目录
        build_dir = Path("build")
        if build_dir.exists():
            shutil.rmtree(build_dir)
            logger.debug(build_dir)
        # 清理.spec文件
        spec_files = list(Path(".").glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()
            logger.debug(spec_file)

    def _run_command(self, args: list[str], success_msg: str | None = None, error_msg: str | None = None):
        """
        运行命令并检查结果

        Args:
            args (list[str]): 命令行参数列表
            success_msg (str | None): 成功时的消息. Defaults to None.
            error_msg (str ｜ None, optional): 错误时的异常消息, 若 None 则不抛出异常. Defaults to None.

        Raises:
            BuildError: 当命令执行失败且 error_msg 不为 None

        Returns:
            如果命令执行成功, 返回标准输出内容; 否则返回 False
        """
        logger.debug(f"Execute: {' '.join(f'{arg}' for arg in args)}")
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        logger.debug(result.stdout.strip())
        if result.returncode != 0:
            if error_msg is not None:
                raise BuildError(f"{error_msg}")
            return False
        if success_msg:
            logger.info(f"{success_msg}")
        return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", "-v", help="指定版本号")
    parser.add_argument("--app-name", "-n", default="MDCx", help="指定应用名称")
    parser.add_argument("--create-dmg", "-dmg", action="store_true", help="创建 DMG 文件 (仅macOS)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")
    args = parser.parse_args()

    if args.no_color:
        console._color_system = None
    if args.debug:
        logger.setLevel(logging.DEBUG)

    manager = BuildManager(app_name=args.app_name, app_version=args.version, create_dmg=args.create_dmg)
    manager.run()


if __name__ == "__main__":
    main()
