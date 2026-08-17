# -*- coding: utf-8 -*-
from .plugin import UserManagerTool

def plugin(ai_model):
    return UserManagerTool(ai_model)
