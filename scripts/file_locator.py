#!/bin/env python
import os


def get_path(name):
    path = "./%s" % name
    if os.path.exists(path):
        return path
    path = "../%s" % name
    if os.path.exists(path):
        return path
    path = "../../%s" % name
    if os.path.exists(path):
        return path
    path = "../../../%s" % name
    if os.path.exists(path):
        return path
    path = "../scripts/%s" % name
    if os.path.exists(path):
        return path
    return name
