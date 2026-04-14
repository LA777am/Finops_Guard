"""
database.py - PostgreSQL database layer for FinOps Guardian
Production-grade implementation for Neon PostgreSQL 17
"""

import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

import pandas as pd
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values, RealDictCursor
from psycopg2 import sql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinOpsDatabase:
    """PostgreSQL database handler for FinOps Guardian"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection pool
        
        Args:
            connection_string: PostgreSQL connection string (Neon format)
                              If None, reads from DATABASE_URL environment variable
        """
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("Database connection string is required")
        
        # Ensure SSL is enabled for Neon
        if 'sslmode' not in self.connection_string.lower():
            self.connection_string += '?sslmode=require' if '?' not in self.connection_string else '&sslmode=require'
        
        # Initialize connection pool (min 1, max 10 connections - suitable for serverless)
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 10, self.connection_string,
                connect_timeout=10,
                application_name='finops_guardian'
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def create_tables(self) -> bool:
        """
        Create all tables and indexes for FinOps Guardian
        
        Returns:
            bool: True if successful, False otherwise
        """
        create_statements = [
            # Table 1: anomaly_logs
            """
            CREATE TABLE IF NOT EXISTS anomaly_logs (
                id BIGSERIAL PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                provider VARCHAR(20) NOT NULL,
                service_category VARCHAR(50) NOT NULL,
                team VARCHAR(50) NOT NULL,
                cost_usd DOUBLE PRECISION,
                is_anomaly BOOLEAN,
                severity_label VARCHAR(10),
                severity_score DOUBLE PRECISION,
                root_cause TEXT,
                llm_insight TEXT,
                recommended_action TEXT,
                estimated_savings VARCHAR(50),
                model_votes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                impact_score DOUBLE PRECISION,
                priority VARCHAR(20)
            )
            """,
            
            # Table 2: forecast_results
            """
            CREATE TABLE IF NOT EXISTS forecast_results (
                id BIGSERIAL PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                provider VARCHAR(20) NOT NULL,
                service_category VARCHAR(50) NOT NULL,
                team VARCHAR(50) NOT NULL,
                forecast_50 DOUBLE PRECISION,
                forecast_90 DOUBLE PRECISION,
                forecast_10 DOUBLE PRECISION,
                horizon_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Table 3: model_metrics
            """
            CREATE TABLE IF NOT EXISTS model_metrics (
                id BIGSERIAL PRIMARY KEY,
                model_name VARCHAR(50),
                f1_score DOUBLE PRECISION,
                precision_score DOUBLE PRECISION,
                recall_score DOUBLE PRECISION,
                mape DOUBLE PRECISION,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Indexes for performance
            "CREATE INDEX IF NOT EXISTS idx_anomaly_date ON anomaly_logs(date)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_provider_service ON anomaly_logs(provider, service_category)",
            "CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_results(date)",
            "CREATE INDEX IF NOT EXISTS idx_forecast_provider_service ON forecast_results(provider, service_category)"
        ]
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for statement in create_statements:
                        cur.execute(statement)
                    conn.commit()
                    logger.info("Tables and indexes created successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def insert_anomalies(self, df: pd.DataFrame) -> int:
        """
        Bulk insert anomaly detection results
        
        Args:
            df: DataFrame with columns matching anomaly_logs table
            
        Returns:
            int: Number of rows inserted
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for anomaly insertion")
            return 0
        
        # Convert is_anomaly from 0/1 to boolean
        df_clean = df.copy()
        if 'is_anomaly' in df_clean.columns:
            df_clean['is_anomaly'] = df_clean['is_anomaly'].astype(bool)

        
        # Ensure date column is datetime                
        if 'date' in df_clean.columns:
            df_clean['date'] = pd.to_datetime(df_clean['date'])
        
        # Prepare columns for insertion
        columns = [
            'date', 'provider', 'service_category', 'team', 'cost_usd',
            'is_anomaly', 'severity_label', 'severity_score',
            'root_cause',
            'llm_insight',
            'recommended_action',
            'estimated_savings',
            'model_votes',
            'impact_score',     # ✅ ADD
            'priority'          # ✅ ADD
        ]
        
        # Convert DataFrame to list of tuples
        values = [tuple(row[col] if pd.notna(row[col]) else None for col in columns) 
                  for _, row in df_clean.iterrows()]
        
        insert_query = """
        INSERT INTO anomaly_logs (
            date, provider, service_category, team, cost_usd,
            is_anomaly, severity_label, severity_score, root_cause,
            llm_insight, recommended_action, estimated_savings,
            model_votes,
            impact_score,
            priority
        ) VALUES %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        insert_query,
                        values,
                        template=None,
                        page_size=1000
                    )
                    conn.commit()
                    rows_inserted = cur.rowcount
                    logger.info(f"Successfully inserted {rows_inserted} anomaly records")
                    return rows_inserted
        except Exception as e:
            logger.error(f"Failed to insert anomalies: {e}")
            raise
    
    def insert_forecasts(self, df: pd.DataFrame) -> int:
        """
        Bulk insert forecast results
        
        Args:
            df: DataFrame with columns matching forecast_results table
            
        Returns:
            int: Number of rows inserted
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for forecast insertion")
            return 0
        
        df_clean = df.copy()
        
        # Ensure date column is datetime
        if 'date' in df_clean.columns:
            df_clean['date'] = pd.to_datetime(df_clean['date'])
        
        # Prepare columns for insertion
        columns = [
            'date', 'provider', 'service_category', 'team',
            'forecast_50', 'forecast_90', 'forecast_10', 'horizon_days'
        ]
        
        # Convert DataFrame to list of tuples
        values = [
            tuple(row[col] if pd.notna(row[col]) else None for col in columns)
            for _, row in df_clean.iterrows()
        ]
        
        insert_query = """
        INSERT INTO forecast_results (
            date, provider, service_category, team,
            forecast_50, forecast_90, forecast_10, horizon_days
        ) VALUES %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, insert_query, values, page_size=1000)
                    conn.commit()
                    rows_inserted = cur.rowcount
                    logger.info(f"Successfully inserted {rows_inserted} forecast records")
                    return rows_inserted
        except Exception as e:
            logger.error(f"Failed to insert forecasts: {e}")
            raise
    
    def insert_metrics(self, metrics_dict: Dict[str, Any]) -> int:
        """
        Insert a single row of model evaluation metrics
        
        Args:
            metrics_dict: Dictionary containing model metrics
                         Required keys: model_name, f1_score, precision_score, 
                                      recall_score, mape
            
        Returns:
            int: ID of inserted row
        """
        required_keys = ['model_name', 'f1_score', 'precision_score', 'recall_score', 'mape']
        for key in required_keys:
            if key not in metrics_dict:
                raise ValueError(f"Missing required metric: {key}")
        
        insert_query = """
        INSERT INTO model_metrics (
            model_name, f1_score, precision_score, recall_score, mape
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        values = (
            metrics_dict['model_name'],
            metrics_dict['f1_score'],
            metrics_dict['precision_score'],
            metrics_dict['recall_score'],
            metrics_dict['mape']
        )
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_query, values)
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Successfully inserted model metrics with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Failed to insert model metrics: {e}")
            raise
    
    def fetch_anomalies(
        self, 
        service: Optional[str] = None, 
        provider: Optional[str] = None, 
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch anomaly records with optional filtering
        
        Args:
            service: Filter by service_category (optional)
            provider: Filter by provider (optional)
            limit: Maximum number of records to return
            
        Returns:
            DataFrame containing anomaly records
        """
        query = """
        SELECT 
            id, date, provider, service_category, team, cost_usd,
            is_anomaly, severity_label, severity_score, root_cause,
            llm_insight, recommended_action, estimated_savings,
            model_votes, created_at,
            impact_score,
            priority
        FROM anomaly_logs
        WHERE 1=1
        """
        params = []
        
        if service:
            query += " AND service_category = %s"
            params.append(service)
        
        if provider:
            query += " AND provider = %s"
            params.append(provider)
        
        query += " ORDER BY date DESC LIMIT %s"
        params.append(limit)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    results = cur.fetchall()
                    df = pd.DataFrame(results)
                    logger.info(f"Fetched {len(df)} anomaly records")
                    return df
        except Exception as e:
            logger.error(f"Failed to fetch anomalies: {e}")
            raise
    
    def fetch_forecasts(
        self, 
        service: Optional[str] = None, 
        provider: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch forecast records with optional filtering
        
        Args:
            service: Filter by service_category (optional)
            provider: Filter by provider (optional)
            limit: Maximum number of records to return
            
        Returns:
            DataFrame containing forecast records
        """
        query = """
        SELECT 
            id, date, provider, service_category, team,
            forecast_50, forecast_90, forecast_10, horizon_days, created_at
        FROM forecast_results
        WHERE 1=1
        """
        params = []
        
        if service:
            query += " AND service_category = %s"
            params.append(service)
        
        if provider:
            query += " AND provider = %s"
            params.append(provider)
        
        query += " ORDER BY date DESC LIMIT %s"
        params.append(limit)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    results = cur.fetchall()
                    df = pd.DataFrame(results)
                    logger.info(f"Fetched {len(df)} forecast records")
                    return df
        except Exception as e:
            logger.error(f"Failed to fetch forecasts: {e}")
            raise
    
    def fetch_latest_metrics(self, model_name: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch latest model evaluation metrics
        
        Args:
            model_name: Filter by model name (optional)
            
        Returns:
            DataFrame containing latest metrics for each model
        """
        if model_name:
            query = """
            SELECT * FROM model_metrics
            WHERE model_name = %s
            ORDER BY created_at DESC
            LIMIT 1
            """
            params = [model_name]
        else:
            query = """
            SELECT DISTINCT ON (model_name) *
            FROM model_metrics
            ORDER BY model_name, created_at DESC
            """
            params = []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    results = cur.fetchall()
                    df = pd.DataFrame(results)
                    logger.info(f"Fetched metrics for {len(df)} models")
                    return df
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            raise
    
    def close_pool(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")


# Convenience functions for backward compatibility
_db_instance = None

def get_db(connection_string: Optional[str] = None) -> FinOpsDatabase:
    """Get or create database instance (singleton pattern)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = FinOpsDatabase(connection_string)
    return _db_instance


def create_tables(connection_string: Optional[str] = None) -> bool:
    """Create all tables and indexes"""
    db = get_db(connection_string)
    return db.create_tables()


def insert_anomalies(df: pd.DataFrame, connection_string: Optional[str] = None) -> int:
    """Insert anomaly detection results"""
    db = get_db(connection_string)
    return db.insert_anomalies(df)


def insert_forecasts(df: pd.DataFrame, connection_string: Optional[str] = None) -> int:
    """Insert forecast results"""
    db = get_db(connection_string)
    return db.insert_forecasts(df)


def insert_metrics(metrics_dict: Dict[str, Any], connection_string: Optional[str] = None) -> int:
    """Insert model evaluation metrics"""
    db = get_db(connection_string)
    return db.insert_metrics(metrics_dict)


def fetch_anomalies(
    service: Optional[str] = None, 
    provider: Optional[str] = None, 
    limit: int = 10000,
    connection_string: Optional[str] = None
) -> pd.DataFrame:
    """Fetch anomaly records"""
    db = get_db(connection_string)
    return db.fetch_anomalies(service, provider, limit)


def fetch_forecasts(
    service: Optional[str] = None, 
    provider: Optional[str] = None,
    connection_string: Optional[str] = None
) -> pd.DataFrame:
    """Fetch forecast records"""
    db = get_db(connection_string)
    return db.fetch_forecasts(service, provider)


# Example usage
if __name__ == "__main__":
    # Example: Set connection string (use environment variable in production)
    # DATABASE_URL = "postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/finops?sslmode=require"
    
    # Initialize database
    db = FinOpsDatabase(os.getenv('DATABASE_URL'))
    
    # Create tables
    db.create_tables()
    
    # Example: Insert anomaly data
    sample_anomalies = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5, freq='D'),
        'provider': ['AWS'] * 5,
        'service_category': ['Compute'] * 5,
        'team': ['Platform'] * 5,
        'cost_usd': [100.50, 102.30, 450.00, 98.20, 101.10],
        'is_anomaly': [0, 0, 1, 0, 0],
        'severity_label': ['low', 'low', 'high', 'low', 'low'],
        'severity_score': [0.1, 0.2, 0.95, 0.1, 0.15],
        'root_cause': [None, None, 'Cost spike in EC2', None, None],
        'model_votes': [3, 3, 5, 3, 3]
    })
    
    # Insert data
    # rows = db.insert_anomalies(sample_anomalies)
    # print(f"Inserted {rows} anomalies")
    
    # Fetch data
    # anomalies_df = db.fetch_anomalies(provider='AWS', limit=10)
    # print(anomalies_df.head())
    
    # Close pool when done
    # db.close_pool()