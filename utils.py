import os
import random
import string
import time
import uuid
from pathlib import Path
from typing import Any
from typing import Optional, Union


def save_file(
        file_path: Union[str, Path],
        content: Any,
        encoding: str = 'utf-8',
        create_parent_dirs: bool = True,
        overwrite: bool = True,
        backup_existing: bool = False,
        verbose: bool = False
) -> tuple[bool, Optional[str]]:
    """
    安全地保存文件内容到指定路径

    Args:
        file_path: 文件路径，可以是字符串或Path对象
        content: 要保存的内容，可以是字符串、字节或可写入的对象
        encoding: 文件编码，默认为utf-8
        create_parent_dirs: 是否自动创建父目录，默认为True
        overwrite: 是否覆盖已存在的文件，默认为True
        backup_existing: 当覆盖文件时是否创建备份，默认为False
        verbose: 是否打印详细信息，默认为False

    Returns:
        tuple[bool, Optional[str]]: (成功状态, 错误信息)
    """
    try:
        # 转换为Path对象
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # 检查路径有效性
        if not path or str(path).strip() == "":
            error_msg = "文件路径不能为空"
            if verbose:
                print(f"错误: {error_msg}")
            return False, error_msg

        # 检查路径是否为目录
        if path.exists() and path.is_dir():
            error_msg = f"路径 '{path}' 是一个目录，不能保存文件"
            if verbose:
                print(f"错误: {error_msg}")
            return False, error_msg

        # 检查文件是否已存在
        if path.exists():
            if not overwrite:
                error_msg = f"文件 '{path}' 已存在且不允许覆盖"
                if verbose:
                    print(f"错误: {error_msg}")
                return False, error_msg
            elif backup_existing:
                # 创建备份文件
                backup_path = path.with_suffix(path.suffix + '.bak')
                try:
                    path.rename(backup_path)
                    if verbose:
                        print(f"已创建备份文件: {backup_path}")
                except Exception as e:
                    warning_msg = f"无法创建备份文件: {e}"
                    if verbose:
                        print(f"警告: {warning_msg}")

        # 创建父目录
        if create_parent_dirs:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if verbose:
                    print(f"已创建目录: {path.parent}")
            except PermissionError:
                error_msg = f"没有权限创建目录: {path.parent}"
                if verbose:
                    print(f"错误: {error_msg}")
                return False, error_msg
            except Exception as e:
                error_msg = f"创建目录时出错: {e}"
                if verbose:
                    print(f"错误: {error_msg}")
                return False, error_msg

        # 准备写入内容
        write_content = content
        if isinstance(content, str):
            # 字符串内容
            mode = 'w'
        elif isinstance(content, bytes):
            # 字节内容
            mode = 'wb'
            encoding = None  # 字节模式不需要编码
        else:
            # 其他类型尝试转换为字符串
            try:
                write_content = str(content)
                mode = 'w'
            except Exception as e:
                error_msg = f"无法处理内容类型: {type(content)}, 错误: {e}"
                if verbose:
                    print(f"错误: {error_msg}")
                return False, error_msg

        # 写入文件
        try:
            with open(path, mode, encoding=encoding) as f:
                f.write(write_content)
            if verbose:
                print(f"文件保存成功: {path}")
            return True, None

        except PermissionError:
            error_msg = f"没有写入权限: {path}"
            if verbose:
                print(f"错误: {error_msg}")
            return False, error_msg
        except UnicodeEncodeError as e:
            error_msg = f"编码错误 (尝试使用不同的编码): {e}"
            if verbose:
                print(f"错误: {error_msg}")
            return False, error_msg
        except IOError as e:
            error_msg = f"IO错误: {e}"
            if verbose:
                print(f"错误: {error_msg}")
            return False, error_msg

    except Exception as e:
        error_msg = f"保存文件时发生未知错误: {e}"
        if verbose:
            print(f"错误: {error_msg}")
        return False, error_msg


def save_file_with_retry(
        file_path: Union[str, Path],
        content: Any,
        max_attempts: int = 3,
        verbose: bool = False,
        **kwargs
) -> tuple[bool, Optional[str]]:
    """
    带重试机制的文件保存函数

    Args:
        file_path: 文件路径
        content: 文件内容
        max_attempts: 最大重试次数
        verbose: 是否打印详细信息
        **kwargs: 传递给save_file的其他参数

    Returns:
        tuple[bool, Optional[str]]: (成功状态, 错误信息)
    """
    for attempt in range(max_attempts):
        _success, error_msg = save_file(file_path, content, verbose=verbose, **kwargs)
        if _success:
            return True, None

        if verbose:
            print(f"保存文件失败，第 {attempt + 1} 次重试... 错误: {error_msg}")

    final_error = f"经过 {max_attempts} 次尝试后仍无法保存文件: {file_path}"
    if verbose:
        print(f"错误: {final_error}")
    return False, final_error


def save_file_silent(
        file_path: Union[str, Path],
        content: Any,
        **kwargs
) -> bool:
    """
    静默保存文件，只返回成功状态，不返回错误信息

    Args:
        file_path: 文件路径
        content: 文件内容
        **kwargs: 其他参数

    Returns:
        bool: 成功返回True，失败返回False
    """
    _success, _ = save_file(file_path, content, verbose=False, **kwargs)
    return _success


def generate_random_filename(
        extension: Optional[str] = None,
        length: int = 12,
        prefix: str = "",
        suffix: str = "",
        directory: Optional[Union[str, Path]] = None,
        max_attempts: int = 10,
        charset: str = "alphanumeric",
        timestamp: bool = False
) -> str:
    """
    生成随机文件名，确保在目标目录中不重复

    Args:
        extension: 文件扩展名 (如: 'txt', 'jpg', 不需要点)
        length: 随机部分长度 (默认: 12)
        prefix: 文件名前缀
        suffix: 文件名后缀 (在扩展名之前)
        directory: 目标目录，用于检查文件名是否已存在
        max_attempts: 最大尝试次数，防止无限循环
        charset: 字符集类型 ('alphanumeric', 'letters', 'digits', 'hex', 'safe')
        timestamp: 是否包含时间戳

    Returns:
        str: 生成的随机文件名

    Raises:
        ValueError: 参数无效时
        RuntimeError: 无法生成唯一文件名时
    """
    # 参数验证
    if length <= 0:
        raise ValueError("长度必须为正整数")

    if max_attempts <= 0:
        raise ValueError("最大尝试次数必须为正整数")

    # 处理扩展名
    if extension is not None:
        extension = extension.strip().lstrip('.')
        if not extension:
            raise ValueError("扩展名不能为空字符串")
        if any(c in extension for c in r'<>:"/\|?*'):
            raise ValueError(f"扩展名包含非法字符: {extension}")

    # 验证目录
    target_dir = None
    if directory is not None:
        target_dir = Path(directory)
        if not target_dir.exists():
            raise ValueError(f"目录不存在: {directory}")
        if not target_dir.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

    # 定义字符集
    charsets = {
        'alphanumeric': string.ascii_letters + string.digits,
        'letters': string.ascii_letters,
        'digits': string.digits,
        'hex': string.hexdigits.lower(),
        'safe': string.ascii_letters + string.digits + '_-'
    }

    if charset not in charsets:
        raise ValueError(f"不支持的字符集类型: {charset}，可选: {list(charsets.keys())}")

    charset_str = charsets[charset]

    # 生成文件名
    for attempt in range(max_attempts):
        try:
            # 生成随机部分
            if charset == 'hex':
                # 使用UUID生成更随机的十六进制字符串
                random_part = uuid.uuid4().hex[:length]
            else:
                random_part = ''.join(random.choices(charset_str, k=length))

            # 构建文件名
            filename_parts = []

            if prefix:
                filename_parts.append(prefix)

            if timestamp:
                timestamp_part = str(int(time.time()))
                filename_parts.append(timestamp_part)

            filename_parts.append(random_part)

            if suffix:
                filename_parts.append(suffix)

            filename = "_".join(filename_parts)

            # 添加扩展名
            if extension is not None:
                filename = f"{filename}.{extension}"

            # 检查文件名是否合法
            if not is_valid_filename(filename):
                continue

            # 检查是否已存在
            if target_dir is not None:
                file_path = target_dir / filename
                if file_path.exists():
                    continue

            return filename

        except Exception as e:
            if attempt == max_attempts - 1:
                raise RuntimeError(f"生成随机文件名时出错: {e}") from e
            continue

    # 如果达到最大尝试次数仍未生成唯一文件名
    raise RuntimeError(f"无法在 {max_attempts} 次尝试内生成唯一文件名")


def is_valid_filename(filename: str) -> bool:
    """
    检查文件名是否合法

    Args:
        filename: 要检查的文件名

    Returns:
        bool: 文件名合法返回True
    """
    if not filename or filename.strip() == "":
        return False

    # Windows和Unix的非法字符
    illegal_chars = r'<>:"/\|?*'

    # 检查非法字符
    if any(char in filename for char in illegal_chars):
        return False

    # 检查保留文件名 (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False

    # 检查文件名长度 (考虑不同文件系统的限制)
    if len(filename) > 255:  # 常见文件系统的限制
        return False

    # 检查不能以点或空格结尾 (Windows限制)
    if filename.endswith(('.', ' ')):
        return False

    return True


def generate_multiple_filenames(
        count: int,
        extension: Optional[str] = None,
        **kwargs
) -> list[str]:
    """
    生成多个随机文件名

    Args:
        count: 要生成的文件名数量
        extension: 文件扩展名
        **kwargs: 传递给generate_random_filename的参数

    Returns:
        list[str]: 生成的随机文件名列表
    """
    if count <= 0:
        raise ValueError("数量必须为正整数")

    filenames = []
    for i in range(count):
        try:
            # 为每个文件添加序号后缀以确保唯一性
            kwargs_with_suffix = kwargs.copy()
            if 'suffix' in kwargs:
                kwargs_with_suffix['suffix'] = f"{kwargs['suffix']}_{i + 1}"
            else:
                kwargs_with_suffix['suffix'] = str(i + 1)

            filename = generate_random_filename(extension=extension, **kwargs_with_suffix)
            filenames.append(filename)
        except Exception as e:
            raise RuntimeError(f"生成第 {i + 1} 个文件名时出错: {e}") from e

    return filenames


def generate_temp_filename(
        extension: Optional[str] = None,
        temp_dir: Optional[Union[str, Path]] = None,
        **kwargs
) -> str:
    """
    生成临时文件的随机文件名

    Args:
        extension: 文件扩展名
        temp_dir: 临时目录，默认为系统临时目录
        **kwargs: 其他参数

    Returns:
        str: 临时文件名
    """
    if temp_dir is None:
        temp_dir = Path(os.environ.get('TEMP', '/tmp'))

    kwargs.setdefault('prefix', 'tmp')
    kwargs.setdefault('timestamp', True)

    return generate_random_filename(
        extension=extension,
        directory=temp_dir,
        **kwargs
    )
