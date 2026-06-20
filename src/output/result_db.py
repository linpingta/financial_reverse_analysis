"""
SQLite 结果存储模块

功能：
- 存储每次分析运行的结果
- 提供历史查询功能
- 支持按日期、行业筛选
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger


class ResultDB:
    """分析结果数据库管理器"""

    def __init__(self, db_path: str = "data/results.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建分析结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    prosperity_pct REAL,
                    valuation_pct REAL,
                    price_pct REAL,
                    divergence_type TEXT,
                    divergence_strength REAL,
                    signal TEXT,
                    score_total REAL,
                    score_level TEXT,
                    risk_warnings TEXT,
                    recommendation TEXT,
                    raw_data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_run_date
                ON analysis_results(run_date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_industry
                ON analysis_results(industry)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON analysis_results(created_at)
            """)

            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")

    def save_result(self, result: Dict[str, Any]) -> int:
        """
        保存单条分析结果

        Args:
            result: 分析结果字典，包含以下字段：
                - run_date: 运行日期 (YYYY-MM-DD)
                - industry: 行业名称
                - prosperity_pct: 景气分位
                - valuation_pct: 估值分位
                - price_pct: 价格分位
                - divergence_type: 背离类型
                - divergence_strength: 背离强度
                - signal: 信号判定
                - score_total: 综合得分
                - score_level: 得分等级
                - risk_warnings: 风险提示
                - recommendation: 操作建议
                - raw_data: 原始数据字典

        Returns:
            插入的记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO analysis_results (
                    run_date, industry, prosperity_pct, valuation_pct, price_pct,
                    divergence_type, divergence_strength, signal,
                    score_total, score_level, risk_warnings, recommendation,
                    raw_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get('run_date', datetime.now().strftime('%Y-%m-%d')),
                result.get('industry', ''),
                result.get('prosperity_pct'),
                result.get('valuation_pct'),
                result.get('price_pct'),
                result.get('divergence_type'),
                result.get('divergence_strength'),
                result.get('signal'),
                result.get('score_total'),
                result.get('score_level'),
                json.dumps(result.get('risk_warnings', []), ensure_ascii=False) if isinstance(result.get('risk_warnings'), list) else result.get('risk_warnings', ''),
                result.get('recommendation'),
                json.dumps(result.get('raw_data', {}), ensure_ascii=False)
            ))

            conn.commit()
            record_id = cursor.lastrowid
            logger.info(f"保存分析结果: 行业={result.get('industry')}, ID={record_id}")
            return record_id

    def save_results_batch(self, results: List[Dict[str, Any]]) -> int:
        """
        批量保存分析结果

        Args:
            results: 分析结果列表

        Returns:
            插入的记录数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            records = []
            for result in results:
                records.append((
                    result.get('run_date', datetime.now().strftime('%Y-%m-%d')),
                    result.get('industry', ''),
                    result.get('prosperity_pct'),
                    result.get('valuation_pct'),
                    result.get('price_pct'),
                    result.get('divergence_type'),
                    result.get('divergence_strength'),
                    result.get('signal'),
                    result.get('score_total'),
                    result.get('score_level'),
                    json.dumps(result.get('risk_warnings', []), ensure_ascii=False) if isinstance(result.get('risk_warnings'), list) else result.get('risk_warnings', ''),
                    result.get('recommendation'),
                    json.dumps(result.get('raw_data', {}), ensure_ascii=False)
                ))

            cursor.executemany("""
                INSERT INTO analysis_results (
                    run_date, industry, prosperity_pct, valuation_pct, price_pct,
                    divergence_type, divergence_strength, signal,
                    score_total, score_level, risk_warnings, recommendation,
                    raw_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)

            conn.commit()
            count = cursor.rowcount
            logger.info(f"批量保存分析结果: {count} 条记录")
            return count

    def query_by_date(self, run_date: str) -> List[Dict[str, Any]]:
        """
        按日期查询分析结果

        Args:
            run_date: 运行日期 (YYYY-MM-DD)

        Returns:
            分析结果列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM analysis_results
                WHERE run_date = ?
                ORDER BY industry
            """, (run_date,))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def query_by_industry(
        self,
        industry: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按行业查询历史分析结果

        Args:
            industry: 行业名称
            limit: 返回记录数量限制

        Returns:
            分析结果列表（按日期倒序）
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM analysis_results
                WHERE industry = ?
                ORDER BY run_date DESC
                LIMIT ?
            """, (industry, limit))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def query_latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询最新的分析结果

        Args:
            limit: 返回记录数量限制

        Returns:
            分析结果列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def query_by_signal(
        self,
        signal: str,
        run_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        按信号类型查询分析结果

        Args:
            signal: 信号类型 (buy/sell/hold)
            run_date: 可选，指定日期

        Returns:
            分析结果列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if run_date:
                cursor.execute("""
                    SELECT * FROM analysis_results
                    WHERE signal = ? AND run_date = ?
                    ORDER BY score_total DESC
                """, (signal, run_date))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_results
                    WHERE signal = ?
                    ORDER BY run_date DESC, score_total DESC
                """, (signal,))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def query_by_score_range(
        self,
        min_score: float,
        max_score: float,
        run_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        按得分范围查询分析结果

        Args:
            min_score: 最低得分
            max_score: 最高得分
            run_date: 可选，指定日期

        Returns:
            分析结果列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if run_date:
                cursor.execute("""
                    SELECT * FROM analysis_results
                    WHERE score_total BETWEEN ? AND ?
                    AND run_date = ?
                    ORDER BY score_total DESC
                """, (min_score, max_score, run_date))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_results
                    WHERE score_total BETWEEN ? AND ?
                    ORDER BY run_date DESC, score_total DESC
                """, (min_score, max_score))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_statistics(self, run_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            run_date: 可选，指定日期

        Returns:
            统计信息字典
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if run_date:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_count,
                        AVG(score_total) as avg_score,
                        MAX(score_total) as max_score,
                        MIN(score_total) as min_score
                    FROM analysis_results
                    WHERE run_date = ?
                """, (run_date,))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_count,
                        AVG(score_total) as avg_score,
                        MAX(score_total) as max_score,
                        MIN(score_total) as min_score
                    FROM analysis_results
                """)

            row = cursor.fetchone()

            # 按信号类型统计
            if run_date:
                cursor.execute("""
                    SELECT signal, COUNT(*) as count
                    FROM analysis_results
                    WHERE run_date = ?
                    GROUP BY signal
                """, (run_date,))
            else:
                cursor.execute("""
                    SELECT signal, COUNT(*) as count
                    FROM analysis_results
                    GROUP BY signal
                """)

            signal_stats = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total_count': row[0],
                'avg_score': round(row[1], 2) if row[1] else 0,
                'max_score': round(row[2], 2) if row[2] else 0,
                'min_score': round(row[3], 2) if row[3] else 0,
                'signal_distribution': signal_stats
            }

    def delete_old_records(self, days: int = 90) -> int:
        """
        删除旧记录

        Args:
            days: 保留最近N天的记录

        Returns:
            删除的记录数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM analysis_results
                WHERE created_at < datetime('now', ?)
            """, (f'-{days} days',))

            conn.commit()
            count = cursor.rowcount
            logger.info(f"删除 {count} 条旧记录（保留最近 {days} 天）")
            return count

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        将数据库行转换为字典

        Args:
            row: 数据库行对象

        Returns:
            字典格式的结果
        """
        result = dict(row)
        # 解析 JSON 字段
        if result.get('raw_data_json'):
            result['raw_data'] = json.loads(result['raw_data_json'])
            del result['raw_data_json']
        return result

    def export_to_dataframe(self, run_date: Optional[str] = None):
        """
        导出为 DataFrame（用于 CSV 导出）

        Args:
            run_date: 可选，指定日期

        Returns:
            pandas.DataFrame
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("需要安装 pandas: pip install pandas")
            return None

        if run_date:
            results = self.query_by_date(run_date)
        else:
            results = self.query_latest(limit=1000)

        # 展平 raw_data
        flat_results = []
        for result in results:
            flat = {k: v for k, v in result.items() if k != 'raw_data'}
            if 'raw_data' in result:
                flat.update(result['raw_data'])
            flat_results.append(flat)

        return pd.DataFrame(flat_results)