# -*- coding: utf-8 -*-

import json
import os
import os.path as osp
import pickle
import shutil
import time
from collections import Callable

from .dicom import sitk, sitk_read_image

PARSER_EXT_DICT = {"pickle": "pkl", "json": "json",
                   "torch": "pth", "sitk": ["dicom", "dcm"]}


def _inverse_dict(d):
    inv_d = {}
    for k, v in d.items():
        if isinstance(v, list):
            inv_d.update({_v: k for _v in v})
        else:
            inv_d[v] = k
    return inv_d


EXT_TO_PARSER_DICT = _inverse_dict(PARSER_EXT_DICT)


def make_dir(*args):
    """
    the one-liner directory creator
    """
    path = osp.join(*[arg.strip(" ") for arg in args])
    if not osp.isdir(path):
        from random import random

        time.sleep(random() * 0.001)
        if not osp.isdir(path):
            os.makedirs(path)
    return path


def read_str(string, default_out=None):
    """
    the one-liner string parser
    """
    def invalid_entry(value):
        return value is None or value == ""

    def invalid_type(value):
        raise ValueError()

    if invalid_entry(string):
        return default_out

    if isinstance(string, str):
        parser = json.loads
    elif isinstance(string, bytes):
        parser = pickle.loads
    else:
        parser = invalid_type
    try:
        out = parser(string)
    except Exception:
        out = default_out
        print(string)
    return out


def load(filename, file_type="auto", **kwargs):
    """
    the one-liner loader
    Args:
        filename (str)
        file_type (str): support types: PARSER_EXT_DICT
    """

    if not isinstance(filename, str):
        return None

    if file_type == "auto":
        ext = filename.rpartition(".")[-1].lower()
        file_type = EXT_TO_PARSER_DICT.get(ext, "unknown")

    if file_type == "json":
        with open(filename, "r") as f:
            result = json.load(f, **kwargs)
    elif file_type == "pickle":
        with open(filename, "rb") as f:
            result = pickle.load(f, **kwargs)
    elif file_type == "torch":
        import torch
        result = torch.load(filename, map_location=torch.device("cpu"))
    elif file_type == "sitk":
        result = sitk_read_image(filename, **kwargs)
    elif file_type == "unknown":
        raise ValueError(f"Unknown ext {filename}")
    else:
        raise NotImplementedError(f"Unknown file_type {file_type}")

    return result


def save(to_be_saved, filename, file_type="auto"):
    """
    the one-liner saver
    Args:
        to_be_saved (any obj)
        filename (str)
        file_type (str): support types: PARSER_EXT_DICT
    """
    if not isinstance(filename, str):
        return None

    if file_type == "auto":
        ext = filename.rpartition(".")[-1]
        file_type = EXT_TO_PARSER_DICT.get(ext, "unknown")

    if file_type == "json":
        with open(filename, "w") as f:
            json.dump(to_be_saved, f)
    elif file_type == "pickle":
        with open(filename, "wb") as f:
            pickle.dump(to_be_saved, f)
    elif file_type == "torch":
        import torch
        torch.save(to_be_saved, f)
    elif file_type == "sitk":
        sitk.WriteImage(to_be_saved, filename)
    elif file_type == "unknown":
        raise ValueError(f"Unknown ext {filename}")
    else:
        raise NotImplementedError(f"Unknown file_type {file_type}")


def recursive_copy(src, dst, softlink=False, overwrite=True, filter_fn=None):
    src_file_list = []

    for root, dirs, files in os.walk(src):
        for filename in files:
            if isinstance(filter_fn, Callable) and not filter_fn(filename):
                continue
            relative_root = root.rpartition(src)[-1].lstrip("/ ")
            src_file_list.append((relative_root, filename))

    make_dir(dst)

    dst_file_list = []
    for root, dirs, files in os.walk(dst):
        for filename in files:
            relative_root = root.rpartition(src)[-1].lstrip("/ ")
            dst_file_list.append((relative_root, filename))

    for f in src_file_list:
        if f in dst_file_list:
            continue
        relative_root = f[0]
        make_dir(dst, relative_root)
        src_path = osp.join(src, *f)
        dst_path = osp.join(dst, *f)
        if osp.exists(dst_path):
            if overwrite:
                if osp.islink(dst_path):
                    if osp.isdir(dst_path):
                        os.rmdir(dst_path)
                    else:
                        os.unlink(dst_path)
                else:
                    os.remove(dst_path)
                print(f"{dst_path} exists, overwrite")
            else:
                print(f"{dst_path} exists, skip")
                continue
        if softlink:
            os.symlink(src_path, dst_path)
        else:
            shutil.copyfile(src_path, dst_path)


__all__ = [k for k in globals().keys() if not k.startswith("_")]
