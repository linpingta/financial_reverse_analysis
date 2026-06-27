# -*- coding: utf-8 -*-
"""
主页面路由
"""
from flask import Blueprint, render_template
from loguru import logger

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页"""
    logger.info("访问首页")
    return render_template('index.html')


@main_bp.route('/analysis')
def analysis():
    """行业分析页面"""
    logger.info("访问行业分析页面")
    return render_template('analysis.html')


@main_bp.route('/history')
def history():
    """历史记录页面"""
    logger.info("访问历史记录页面")
    return render_template('history.html')


@main_bp.route('/export')
def export():
    """数据导出页面"""
    logger.info("访问数据导出页面")
    return render_template('export.html')


@main_bp.route('/industry/<name>')
def industry_detail(name):
    """行业详情页面"""
    logger.info(f"访问行业详情页面: {name}")
    return render_template('industry_detail.html', industry_name=name)


@main_bp.route('/settings')
def settings():
    """系统配置页面"""
    logger.info("访问系统配置页面")
    return render_template('settings.html')