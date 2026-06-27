# -*- coding: utf-8 -*-
"""
API路由
"""
from flask import Blueprint, jsonify, request
from loguru import logger
from datetime import datetime

from ..utils.task_manager import task_manager
from ..utils.helpers import get_industries_list, format_datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/industries', methods=['GET'])
def get_industries():
    """获取行业列表"""
    try:
        industries = get_industries_list()
        return jsonify({
            'success': True,
            'data': industries
        })
    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analyze', methods=['POST'])
def start_analyze():
    """启动分析任务"""
    try:
        data = request.get_json()
        
        mode = data.get('mode', 'all')
        industries = data.get('industries', [])
        save_db = data.get('save_db', True)
        generate_report = data.get('generate_report', False)
        
        logger.info(f"启动分析任务: mode={mode}, industries={industries}")
        
        def run_analysis():
            """执行分析任务（占位函数）"""
            import time
            total = len(industries) if industries else 10
            
            for i in range(total):
                time.sleep(1)
                progress = int((i + 1) / total * 100)
                task_manager.update_progress(
                    task_id,
                    progress,
                    f'正在分析第 {i+1}/{total} 个行业',
                    industries[i] if industries else f'行业{i+1}'
                )
            
            return {
                'total': total,
                'mode': mode,
                'industries': industries,
                'completed_at': datetime.now().isoformat()
            }
        
        task_id = task_manager.create_task(run_analysis)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'pending'
        })
    except Exception as e:
        logger.error(f"启动分析任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analyze/status/<task_id>', methods=['GET'])
def get_analyze_status(task_id):
    """查询分析任务状态"""
    try:
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        response = {
            'success': True,
            'task_id': task_id,
            'status': task_status['status'],
            'progress': task_status['progress'],
            'message': task_status.get('message', ''),
            'current_item': task_status.get('current_item', '')
        }
        
        if task_status['status'] == 'completed':
            response['result'] = task_status['result']
        elif task_status['status'] == 'failed':
            response['error'] = task_status['error']
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analyze/result/<task_id>', methods=['GET'])
def get_analyze_result(task_id):
    """获取分析结果"""
    try:
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        if task_status['status'] != 'completed':
            return jsonify({
                'success': False,
                'error': f'任务尚未完成，当前状态: {task_status["status"]}'
            }), 400
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'result': task_status['result']
        })
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/history', methods=['GET'])
def get_history():
    """查询历史记录"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        date = request.args.get('date')
        industry = request.args.get('industry')
        signal = request.args.get('signal')
        
        logger.info(f"查询历史记录: page={page}, limit={limit}")
        
        mock_data = {
            'total': 50,
            'page': page,
            'limit': limit,
            'records': [
                {
                    'id': i,
                    'run_date': '2024-01-15',
                    'industry': f'行业{i}',
                    'signal': 'buy' if i % 3 == 0 else ('sell' if i % 3 == 1 else 'hold'),
                    'score': 70 + i,
                    'pe_percentile': 30.5 + i,
                    'pb_percentile': 25.3 + i
                }
                for i in range((page - 1) * limit, min(page * limit, 50))
            ]
        }
        
        return jsonify({
            'success': True,
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"查询历史记录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/history/<int:record_id>', methods=['GET'])
def get_history_detail(record_id):
    """查询历史记录详情"""
    try:
        logger.info(f"查询历史记录详情: id={record_id}")
        
        mock_data = {
            'id': record_id,
            'run_date': '2024-01-15',
            'industry': '航空机场',
            'signal': 'buy',
            'score': 85,
            'pe_percentile': 25.5,
            'pb_percentile': 20.3,
            'details': {
                'pe_current': 15.2,
                'pb_current': 1.5,
                'divergence': -0.8
            }
        }
        
        return jsonify({
            'success': True,
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"查询历史记录详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        logger.info("获取统计数据")
        
        mock_data = {
            'total_records': 150,
            'buy_signals': 45,
            'sell_signals': 20,
            'hold_signals': 85,
            'avg_score': 62.5,
            'top_industries': [
                {'name': '航空机场', 'score': 85},
                {'name': '生猪养殖', 'score': 82},
                {'name': '光伏设备', 'score': 78},
                {'name': '锂电池', 'score': 75},
                {'name': '半导体', 'score': 72}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export', methods=['POST'])
def create_export():
    """生成导出文件"""
    try:
        data = request.get_json()
        
        format_type = data.get('format', 'csv')
        filters = data.get('filters', {})
        
        logger.info(f"生成导出文件: format={format_type}")
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/api/export/download/{filename}'
        })
    except Exception as e:
        logger.error(f"生成导出文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export/download/<filename>', methods=['GET'])
def download_export(filename):
    """下载导出文件"""
    try:
        logger.info(f"下载导出文件: {filename}")
        
        from flask import send_from_directory
        from pathlib import Path
        
        export_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'results'
        
        return send_from_directory(export_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"下载导出文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/system', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        logger.info("获取系统状态")
        
        mock_data = {
            'version': '1.0.0',
            'status': 'running',
            'database': 'connected',
            'cache': 'enabled',
            'last_update': datetime.now().isoformat(),
            'active_tasks': len(task_manager.get_all_tasks())
        }
        
        return jsonify({
            'success': True,
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500