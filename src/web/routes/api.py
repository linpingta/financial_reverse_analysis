# -*- coding: utf-8 -*-
"""
API路由 - 集成真实分析引擎、数据库和导出器
"""
from flask import Blueprint, jsonify, request
from loguru import logger
from datetime import datetime
from pathlib import Path

from ..utils.task_manager import task_manager
from ..utils.helpers import get_industries_list, format_datetime
from ..app import push_progress, push_task_complete, push_task_error

from src.output.result_db import ResultDB
from src.output.result_exporter import ResultExporter
from src.analysis.analysis_engine import AnalysisEngine
from src.data.industry_mapper import IndustryMapper

api_bp = Blueprint('api', __name__)

# 初始化核心模块
result_db = ResultDB()
exporter = ResultExporter()
analysis_engine = AnalysisEngine()
industry_mapper = IndustryMapper()


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
    """启动分析任务 - 真实分析引擎"""
    try:
        data = request.get_json()

        mode = data.get('mode', 'all')
        industries = data.get('industries', [])
        save_db = data.get('save_db', True)
        generate_report = data.get('generate_report', False)

        logger.info(f"启动分析任务: mode={mode}, industries={industries}")

        # 获取行业列表
        if mode == 'all':
            target_industries = industry_mapper.get_all_names()
        else:
            target_industries = industries

        def run_analysis():
            """执行真实分析任务"""
            results = []
            total = len(target_industries)
            run_date = datetime.now().strftime('%Y-%m-%d')

            for i, industry_name in enumerate(target_industries):
                try:
                    # 获取行业映射信息
                    mapping = industry_mapper.get_mapping(industry_name)
                    if not mapping:
                        logger.warning(f"行业映射不存在: {industry_name}")
                        continue

                    # 模拟数据（阶段2使用模拟数据，阶段6将接入真实数据源）
                    mock_data = {
                        'prosperity_percentile': 20.0 + (i * 10 % 60),  # 模拟景气分位
                        'valuation_percentile': 25.0 + (i * 8 % 70),    # 模拟估值分位
                        'price_percentile': 30.0 + (i * 12 % 65),       # 模拟价格分位
                        'current_pe': 15.0 + (i * 2 % 20),
                        'current_pb': 1.5 + (i * 0.3 % 2),
                    }

                    # 调用真实分析引擎
                    analysis_result = analysis_engine.analyze_industry(
                        industry_name=industry_name,
                        sw_code=mapping.sw_index_code,
                        pe_percentile=mock_data['valuation_percentile'],
                        pb_percentile=mock_data['valuation_percentile'] + 5,
                        price_change=None,
                        price_trend='下降',
                        prosperity_percentile=mock_data['prosperity_percentile'],
                        valuation_percentile=mock_data['valuation_percentile'],
                        price_percentile=mock_data['price_percentile'],
                        current_pe=mock_data['current_pe'],
                        current_pb=mock_data['current_pb'],
                    )

                    # 转换为数据库存储格式
                    result_dict = {
                        'run_date': run_date,
                        'industry': industry_name,
                        'prosperity_pct': mock_data['prosperity_percentile'],
                        'valuation_pct': mock_data['valuation_percentile'],
                        'price_pct': mock_data['price_percentile'],
                        'divergence_type': analysis_result.divergence_data.get('divergence_type', ''),
                        'divergence_strength': analysis_result.divergence_data.get('divergence_strength', 0.0),
                        'signal': analysis_result.signal_data.get('signal_code', 'hold'),
                        'score_total': analysis_result.scoring_data.get('overall_score', 0.0),
                        'score_level': analysis_result.scoring_data.get('level', '观察'),
                        'risk_warnings': analysis_result.risk_data.get('warnings', []),
                        'recommendation': analysis_result.signal_data.get('recommendation', ''),
                        'raw_data': mock_data,
                    }

                    # 保存到数据库
                    if save_db:
                        result_db.save_result(result_dict)

                    results.append(result_dict)

                    # 更新进度并推送
                    progress = int((i + 1) / total * 100)
                    task_manager.update_progress(
                        task_id,
                        progress,
                        f'正在分析 {industry_name}',
                        industry_name
                    )

                    # 通过 WebSocket 推送进度
                    push_progress(
                        task_id,
                        progress,
                        f'正在分析 {industry_name}',
                        industry_name
                    )

                except Exception as e:
                    logger.error(f"分析行业 {industry_name} 失败: {e}")

            # 生成报告（可选）
            if generate_report and results:
                try:
                    report_filename = f"分析报告_{run_date}"
                    exporter.export_markdown(results, filename=report_filename)
                    logger.info(f"报告已生成: {report_filename}.md")
                except Exception as e:
                    logger.error(f"生成报告失败: {e}")

            return {
                'total': total,
                'completed': len(results),
                'run_date': run_date,
                'mode': mode,
                'industries': target_industries,
                'results': results,
                'completed_at': datetime.now().isoformat()
            }

        task_id = task_manager.create_task(run_analysis)

        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'pending',
            'total_industries': len(target_industries)
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
    """查询历史记录 - 真实数据库查询"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        date = request.args.get('date')
        industry = request.args.get('industry')
        signal = request.args.get('signal')

        logger.info(f"查询历史记录: page={page}, limit={limit}, date={date}, industry={industry}, signal={signal}")

        # 根据查询条件调用不同的查询方法
        results = []

        if date:
            # 按日期查询
            results = result_db.query_by_date(date)
        elif industry:
            # 按行业查询
            results = result_db.query_by_industry(industry, limit=100)
        elif signal:
            # 按信号查询
            results = result_db.query_by_signal(signal)
        else:
            # 查询最新记录
            results = result_db.query_latest(limit=100)

        # 分页处理
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        page_results = results[start:end]

        # 格式化返回数据
        records = []
        for idx, result in enumerate(page_results):
            records.append({
                'id': result.get('id', start + idx),
                'run_date': result.get('run_date', ''),
                'industry': result.get('industry', ''),
                'signal': result.get('signal', 'hold'),
                'score_total': result.get('score_total', 0),
                'score_level': result.get('score_level', ''),
                'prosperity_pct': result.get('prosperity_pct'),
                'valuation_pct': result.get('valuation_pct'),
                'price_pct': result.get('price_pct'),
                'divergence_type': result.get('divergence_type', ''),
                'recommendation': result.get('recommendation', ''),
            })

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'page': page,
                'limit': limit,
                'records': records
            }
        })
    except Exception as e:
        logger.error(f"查询历史记录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/history/<int:record_id>', methods=['GET'])
def get_history_detail(record_id):
    """查询历史记录详情 - 真实数据库查询"""
    try:
        logger.info(f"查询历史记录详情: id={record_id}")

        # 从数据库查询所有记录，找到对应ID
        # 注：ResultDB 目前不支持按ID查询，需要扩展或遍历查找
        all_results = result_db.query_latest(limit=1000)

        # 查找指定ID的记录
        target_result = None
        for result in all_results:
            if result.get('id') == record_id:
                target_result = result
                break

        if not target_result:
            return jsonify({
                'success': False,
                'error': '记录不存在'
            }), 404

        # 格式化详情数据
        detail_data = {
            'id': target_result.get('id'),
            'run_date': target_result.get('run_date', ''),
            'industry': target_result.get('industry', ''),
            'signal': target_result.get('signal', 'hold'),
            'score_total': target_result.get('score_total', 0),
            'score_level': target_result.get('score_level', ''),
            'prosperity_pct': target_result.get('prosperity_pct'),
            'valuation_pct': target_result.get('valuation_pct'),
            'price_pct': target_result.get('price_pct'),
            'divergence_type': target_result.get('divergence_type', ''),
            'divergence_strength': target_result.get('divergence_strength', 0.0),
            'risk_warnings': target_result.get('risk_warnings', []),
            'recommendation': target_result.get('recommendation', ''),
            'raw_data': target_result.get('raw_data', {}),
            'created_at': target_result.get('created_at', ''),
        }

        return jsonify({
            'success': True,
            'data': detail_data
        })
    except Exception as e:
        logger.error(f"查询历史记录详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计数据 - 真实数据库统计"""
    try:
        logger.info("获取统计数据")

        # 从数据库获取统计信息
        stats_data = result_db.get_statistics()

        # 查询评分最高的行业（top 5）
        latest_results = result_db.query_latest(limit=100)
        sorted_results = sorted(
            latest_results,
            key=lambda r: r.get('score_total', 0),
            reverse=True
        )
        top_industries = [
            {
                'name': r.get('industry', ''),
                'score': r.get('score_total', 0),
                'signal': r.get('signal', 'hold'),
            }
            for r in sorted_results[:5]
        ]

        # 信号分布统计
        signal_distribution = stats_data.get('signal_distribution', {})
        buy_signals = signal_distribution.get('buy', 0)
        sell_signals = signal_distribution.get('sell', 0)
        hold_signals = signal_distribution.get('hold', 0)

        return jsonify({
            'success': True,
            'data': {
                'total_records': stats_data.get('total_count', 0),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'avg_score': stats_data.get('avg_score', 0),
                'max_score': stats_data.get('max_score', 0),
                'min_score': stats_data.get('min_score', 0),
                'top_industries': top_industries,
            }
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export', methods=['POST'])
def create_export():
    """生成导出文件 - 真实导出器"""
    try:
        data = request.get_json()

        format_type = data.get('format', 'csv')
        filters = data.get('filters', {})

        logger.info(f"生成导出文件: format={format_type}, filters={filters}")

        # 根据filters查询数据
        results = []

        if 'date' in filters:
            results = result_db.query_by_date(filters['date'])
        elif 'industry' in filters:
            results = result_db.query_by_industry(filters['industry'], limit=1000)
        elif 'signal' in filters:
            results = result_db.query_by_signal(filters['signal'])
        else:
            # 导出全部最新数据
            results = result_db.query_latest(limit=1000)

        if not results:
            return jsonify({
                'success': False,
                'error': '没有数据可导出'
            }), 400

        # 生成文件名
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 根据格式调用导出器
        exported_path = None

        if format_type == 'csv':
            exported_path = exporter.export_csv(results, filename=filename)
        elif format_type == 'excel':
            exported_path = exporter.export_excel(results, filename=filename)
        elif format_type == 'markdown':
            exported_path = exporter.export_markdown(results, filename=filename)
        else:
            return jsonify({
                'success': False,
                'error': f'不支持格式: {format_type}'
            }), 400

        if not exported_path:
            return jsonify({
                'success': False,
                'error': '导出失败'
            }), 500

        # 提取文件名（不含路径）
        export_filename = Path(exported_path).name

        return jsonify({
            'success': True,
            'filename': export_filename,
            'download_url': f'/api/export/download/{export_filename}',
            'total_records': len(results)
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


@api_bp.route('/industry/<name>', methods=['GET'])
def get_industry_detail(name):
    """查询特定行业的详细历史数据"""
    try:
        logger.info(f"查询行业详情: {name}")

        # 查询该行业的历史记录
        results = result_db.query_by_industry(name, limit=50)

        if not results:
            return jsonify({
                'success': False,
                'error': '该行业暂无历史数据'
            }), 404

        # 计算统计数据
        scores = [r.get('score_total', 0) for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0

        # 最新一条记录作为当前状态
        latest = results[0] if results else None

        # 获取行业映射信息
        mapping = industry_mapper.get_mapping(name)

        return jsonify({
            'success': True,
            'data': {
                'industry_name': name,
                'sw_code': mapping.sw_index_code if mapping else '',
                'latest_result': latest,
                'history_count': len(results),
                'avg_score': round(avg_score, 2),
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'history_records': results[:10],  # 最近10条
                'benchmarks': mapping.benchmarks if mapping else [],
            }
        })
    except Exception as e:
        logger.error(f"查询行业详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500