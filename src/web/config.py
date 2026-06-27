# -*- coding: utf-8 -*-
"""
Web应用配置模块
"""
import os
from pathlib import Path


class Config:
    """Flask应用配置"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    BASE_DIR = Path(__file__).parent.parent.parent
    
    DATABASE_PATH = str(BASE_DIR / 'data' / 'results.db')
    
    RESULTS_DIR = str(BASE_DIR / 'data' / 'results')
    
    CACHE_DIR = str(BASE_DIR / 'data' / 'cache')
    
    REPORTS_DIR = str(BASE_DIR / 'reports')
    
    JSON_AS_ASCII = False
    
    JSON_SORT_KEYS = False
    
    SOCKETIO_ASYNC_MODE = 'threading'
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    TEMPLATES_AUTO_RELOAD = True
    
    SEND_FILE_MAX_AGE_DEFAULT = 0


class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    
    DEBUG = False
    
    TESTING = False
    
    TEMPLATES_AUTO_RELOAD = False


class TestingConfig(Config):
    """测试环境配置"""
    
    DEBUG = True
    
    TESTING = True
    
    DATABASE_PATH = ':memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}