"""
Data validation utilities for the data collection agent.

This module provides functionality for validating data quality, detecting anomalies,
and ensuring data integrity across different exchanges and data types.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class DataValidationResult(Enum):
    """Data validation result types."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    MISSING = "missing"


@dataclass
class ValidationError:
    """Represents a data validation error."""
    field: str
    message: str
    severity: str
    value: Any
    expected: Any


@dataclass
class ValidationReport:
    """Complete validation report for data."""
    data_type: str
    exchange: str
    symbol: str
    timestamp: datetime
    result: DataValidationResult
    errors: List[ValidationError]
    accuracy_score: float
    completeness_score: float
    timeliness_score: float
    overall_score: float


class DataValidator:
    """Validates data quality and integrity."""

    def __init__(self, accuracy_threshold: float = 0.99, completeness_threshold: float = 0.99):
        self.logger = logging.getLogger(__name__)
        self.accuracy_threshold = accuracy_threshold
        self.completeness_threshold = completeness_threshold

        # Validation rules
        self.ohlcv_rules = {
            'required_fields': ['timestamp', 'open', 'high', 'low', 'close', 'volume'],
            'numeric_fields': ['open', 'high', 'low', 'close', 'volume'],
            'positive_fields': ['volume'],
            'price_consistency': 'high >= low >= close >= open',
            'timestamp_future': False
        }

        self.orderbook_rules = {
            'required_fields': ['bids', 'asks'],
            'array_fields': ['bids', 'asks'],
            'bid_ask_structure': 'price < amount for each level',
            'bid_ask_order': 'bid prices <= ask prices'
        }

        self.trade_rules = {
            'required_fields': ['timestamp', 'price', 'amount', 'side'],
            'numeric_fields': ['price', 'amount'],
            'positive_fields': ['price', 'amount'],
            'side_values': ['buy', 'sell'],
            'timestamp_future': False
        }

        self.ticker_rules = {
            'required_fields': ['symbol', 'last', 'bid', 'ask', 'volume'],
            'numeric_fields': ['last', 'bid', 'ask', 'volume', 'high', 'low', 'change'],
            'positive_fields': ['last', 'bid', 'ask', 'volume'],
            'bid_ask_order': 'bid <= ask',
            'price_sanity': 'price within reasonable bounds'
        }

    def validate_ohlcv(self, data: List[List], exchange: str, symbol: str) -> ValidationReport:
        """Validate OHLCV data."""
        errors = []
        accuracy_score = 1.0
        completeness_score = 1.0
        timeliness_score = 1.0

        try:
            # Check if data is empty
            if not data:
                errors.append(ValidationError(
                    'data', 'Empty OHLCV data', 'error', None, 'Non-empty data'
                ))
                return self._create_report(
                    'ohlcv', exchange, symbol, DataValidationResult.INVALID,
                    errors, 0, 0, 1, 0
                )

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Check data completeness
            completeness_score, completeness_errors = self._check_completeness(df, self.ohlcv_rules)
            errors.extend(completeness_errors)

            # Check data accuracy
            accuracy_score, accuracy_errors = self._check_ohlcv_accuracy(df)
            errors.extend(accuracy_errors)

            # Check data timeliness
            timeliness_score, timeliness_errors = self._check_timeliness(df, 'timestamp')
            errors.extend(timeliness_errors)

            # Calculate overall score
            overall_score = (accuracy_score + completeness_score + timeliness_score) / 3

            # Determine result
            result = self._determine_result(overall_score, errors)

            return self._create_report(
                'ohlcv', exchange, symbol, result, errors,
                accuracy_score, completeness_score, timeliness_score, overall_score
            )

        except Exception as e:
            self.logger.error(f"Error validating OHLCV data: {e}")
            errors.append(ValidationError(
                'validation', f'Validation error: {str(e)}', 'error', None, 'Successful validation'
            ))
            return self._create_report(
                'ohlcv', exchange, symbol, DataValidationResult.INVALID,
                errors, 0, 0, 1, 0
            )

    def validate_orderbook(self, data: Dict, exchange: str, symbol: str) -> ValidationReport:
        """Validate order book data."""
        errors = []
        accuracy_score = 1.0
        completeness_score = 1.0
        timeliness_score = 1.0

        try:
            # Check if data is empty
            if not data:
                errors.append(ValidationError(
                    'data', 'Empty order book data', 'error', None, 'Non-empty data'
                ))
                return self._create_report(
                    'orderbook', exchange, symbol, DataValidationResult.INVALID,
                    errors, 0, 0, 1, 0
                )

            # Check required fields
            completeness_score, completeness_errors = self._check_dict_completeness(
                data, self.orderbook_rules
            )
            errors.extend(completeness_errors)

            # Check bids and asks structure
            if 'bids' in data and 'asks' in data:
                accuracy_score, accuracy_errors = self._check_orderbook_accuracy(data)
                errors.extend(accuracy_errors)
            else:
                accuracy_score = 0
                errors.append(ValidationError(
                    'structure', 'Missing bids or asks', 'error', data, 'Both bids and asks required'
                ))

            # Check timestamp if available
            if 'timestamp' in data:
                timeliness_score, timeliness_errors = self._check_dict_timeliness(data, 'timestamp')
                errors.extend(timeliness_errors)

            # Calculate overall score
            overall_score = (accuracy_score + completeness_score + timeliness_score) / 3

            # Determine result
            result = self._determine_result(overall_score, errors)

            return self._create_report(
                'orderbook', exchange, symbol, result, errors,
                accuracy_score, completeness_score, timeliness_score, overall_score
            )

        except Exception as e:
            self.logger.error(f"Error validating order book data: {e}")
            errors.append(ValidationError(
                'validation', f'Validation error: {str(e)}', 'error', None, 'Successful validation'
            ))
            return self._create_report(
                'orderbook', exchange, symbol, DataValidationResult.INVALID,
                errors, 0, 0, 1, 0
            )

    def validate_trades(self, data: List[Dict], exchange: str, symbol: str) -> ValidationReport:
        """Validate trades data."""
        errors = []
        accuracy_score = 1.0
        completeness_score = 1.0
        timeliness_score = 1.0

        try:
            # Check if data is empty
            if not data:
                errors.append(ValidationError(
                    'data', 'Empty trades data', 'error', None, 'Non-empty data'
                ))
                return self._create_report(
                    'trades', exchange, symbol, DataValidationResult.INVALID,
                    errors, 0, 0, 1, 0
                )

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(data)

            # Check data completeness
            completeness_score, completeness_errors = self._check_completeness(df, self.trade_rules)
            errors.extend(completeness_errors)

            # Check data accuracy
            accuracy_score, accuracy_errors = self._check_trades_accuracy(df)
            errors.extend(accuracy_errors)

            # Check data timeliness
            timeliness_score, timeliness_errors = self._check_timeliness(df, 'timestamp')
            errors.extend(timeliness_errors)

            # Calculate overall score
            overall_score = (accuracy_score + completeness_score + timeliness_score) / 3

            # Determine result
            result = self._determine_result(overall_score, errors)

            return self._create_report(
                'trades', exchange, symbol, result, errors,
                accuracy_score, completeness_score, timeliness_score, overall_score
            )

        except Exception as e:
            self.logger.error(f"Error validating trades data: {e}")
            errors.append(ValidationError(
                'validation', f'Validation error: {str(e)}', 'error', None, 'Successful validation'
            ))
            return self._create_report(
                'trades', exchange, symbol, DataValidationResult.INVALID,
                errors, 0, 0, 1, 0
            )

    def validate_ticker(self, data: Dict, exchange: str, symbol: str) -> ValidationReport:
        """Validate ticker data."""
        errors = []
        accuracy_score = 1.0
        completeness_score = 1.0
        timeliness_score = 1.0

        try:
            # Check if data is empty
            if not data:
                errors.append(ValidationError(
                    'data', 'Empty ticker data', 'error', None, 'Non-empty data'
                ))
                return self._create_report(
                    'ticker', exchange, symbol, DataValidationResult.INVALID,
                    errors, 0, 0, 1, 0
                )

            # Check required fields
            completeness_score, completeness_errors = self._check_dict_completeness(
                data, self.ticker_rules
            )
            errors.extend(completeness_errors)

            # Check data accuracy
            accuracy_score, accuracy_errors = self._check_ticker_accuracy(data)
            errors.extend(accuracy_errors)

            # Check timestamp if available
            if 'timestamp' in data:
                timeliness_score, timeliness_errors = self._check_dict_timeliness(data, 'timestamp')
                errors.extend(timeliness_errors)

            # Calculate overall score
            overall_score = (accuracy_score + completeness_score + timeliness_score) / 3

            # Determine result
            result = self._determine_result(overall_score, errors)

            return self._create_report(
                'ticker', exchange, symbol, result, errors,
                accuracy_score, completeness_score, timeliness_score, overall_score
            )

        except Exception as e:
            self.logger.error(f"Error validating ticker data: {e}")
            errors.append(ValidationError(
                'validation', f'Validation error: {str(e)}', 'error', None, 'Successful validation'
            ))
            return self._create_report(
                'ticker', exchange, symbol, DataValidationResult.INVALID,
                errors, 0, 0, 1, 0
            )

    def _check_completeness(self, df: pd.DataFrame, rules: Dict) -> Tuple[float, List[ValidationError]]:
        """Check data completeness for DataFrame."""
        errors = []
        required_fields = rules.get('required_fields', [])

        for field in required_fields:
            if field not in df.columns:
                errors.append(ValidationError(
                    field, f'Missing required field: {field}', 'error', None, 'Field present'
                ))
            elif df[field].isna().any():
                missing_count = df[field].isna().sum()
                errors.append(ValidationError(
                    field, f'Missing values in field: {field} ({missing_count} missing)', 'warning',
                    missing_count, 'No missing values'
                ))

        # Calculate completeness score
        total_required = len(required_fields)
        present_fields = sum(1 for field in required_fields if field in df.columns)
        completeness = present_fields / total_required if total_required > 0 else 0

        return completeness, errors

    def _check_dict_completeness(self, data: Dict, rules: Dict) -> Tuple[float, List[ValidationError]]:
        """Check data completeness for dictionary."""
        errors = []
        required_fields = rules.get('required_fields', [])

        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(
                    field, f'Missing required field: {field}', 'error', None, 'Field present'
                ))
            elif data[field] is None:
                errors.append(ValidationError(
                    field, f'Null value in field: {field}', 'warning', None, 'Non-null value'
                ))

        # Calculate completeness score
        total_required = len(required_fields)
        present_fields = sum(1 for field in required_fields if field in data and data[field] is not None)
        completeness = present_fields / total_required if total_required > 0 else 0

        return completeness, errors

    def _check_ohlcv_accuracy(self, df: pd.DataFrame) -> Tuple[float, List[ValidationError]]:
        """Check OHLCV data accuracy."""
        errors = []

        # Check numeric fields
        numeric_fields = self.ohlcv_rules.get('numeric_fields', [])
        for field in numeric_fields:
            if field in df.columns:
                try:
                    pd.to_numeric(df[field])
                except ValueError:
                    errors.append(ValidationError(
                        field, f'Non-numeric values in field: {field}', 'error', 'mixed', 'numeric'
                    ))

        # Check positive fields
        positive_fields = self.ohlcv_rules.get('positive_fields', [])
        for field in positive_fields:
            if field in df.columns:
                negative_count = (df[field] < 0).sum()
                if negative_count > 0:
                    errors.append(ValidationError(
                        field, f'Negative values in field: {field} ({negative_count} negative)', 'warning',
                        negative_count, 'All positive'
                    ))

        # Check price consistency
        if all(field in df.columns for field in ['open', 'high', 'low', 'close']):
            inconsistent_count = (
                (df['high'] < df['low']) |
                (df['low'] < df['close']) |
                (df['close'] < df['open']) |
                (df['high'] < df['open']) |
                (df['high'] < df['close'])
            ).sum()

            if inconsistent_count > 0:
                errors.append(ValidationError(
                    'prices', f'Inconsistent price relationships ({inconsistent_count} rows)', 'warning',
                    inconsistent_count, 'Consistent OHLC'
                ))

        # Calculate accuracy score
        total_checks = len(numeric_fields) + len(positive_fields) + 1  # +1 for price consistency
        passed_checks = total_checks - len([e for e in errors if e.severity == 'error'])
        accuracy = passed_checks / total_checks if total_checks > 0 else 0

        return accuracy, errors

    def _check_orderbook_accuracy(self, data: Dict) -> Tuple[float, List[ValidationError]]:
        """Check order book data accuracy."""
        errors = []

        # Check bids structure
        if 'bids' in data:
            if not isinstance(data['bids'], list):
                errors.append(ValidationError(
                    'bids', 'Bids should be a list', 'error', type(data['bids']), 'list'
                ))
            else:
                for i, bid in enumerate(data['bids']):
                    if len(bid) != 2:
                        errors.append(ValidationError(
                            f'bids[{i}]', f'Invalid bid structure at index {i}', 'error', len(bid), '[price, amount]'
                        ))
                    elif bid[0] <= 0 or bid[1] <= 0:
                        errors.append(ValidationError(
                            f'bids[{i}]', f'Invalid bid values at index {i}', 'error', bid, 'positive values'
                        ))

        # Check asks structure
        if 'asks' in data:
            if not isinstance(data['asks'], list):
                errors.append(ValidationError(
                    'asks', 'Asks should be a list', 'error', type(data['asks']), 'list'
                ))
            else:
                for i, ask in enumerate(data['asks']):
                    if len(ask) != 2:
                        errors.append(ValidationError(
                            f'asks[{i}]', f'Invalid ask structure at index {i}', 'error', len(ask), '[price, amount]'
                        ))
                    elif ask[0] <= 0 or ask[1] <= 0:
                        errors.append(ValidationError(
                            f'asks[{i}]', f'Invalid ask values at index {i}', 'error', ask, 'positive values'
                        ))

        # Check bid-ask spread
        if 'bids' in data and 'asks' in data and data['bids'] and data['asks']:
            best_bid = data['bids'][0][0]
            best_ask = data['asks'][0][0]
            if best_bid >= best_ask:
                errors.append(ValidationError(
                    'spread', f'Invalid bid-ask spread: bid={best_bid}, ask={best_ask}', 'error',
                    (best_bid, best_ask), 'bid < ask'
                ))

        # Calculate accuracy score
        total_checks = 3  # bids, asks, spread
        passed_checks = total_checks - len([e for e in errors if e.severity == 'error'])
        accuracy = passed_checks / total_checks

        return accuracy, errors

    def _check_trades_accuracy(self, df: pd.DataFrame) -> Tuple[float, List[ValidationError]]:
        """Check trades data accuracy."""
        errors = []

        # Check numeric fields
        numeric_fields = self.trade_rules.get('numeric_fields', [])
        for field in numeric_fields:
            if field in df.columns:
                try:
                    pd.to_numeric(df[field])
                except ValueError:
                    errors.append(ValidationError(
                        field, f'Non-numeric values in field: {field}', 'error', 'mixed', 'numeric'
                    ))

        # Check positive fields
        positive_fields = self.trade_rules.get('positive_fields', [])
        for field in positive_fields:
            if field in df.columns:
                negative_count = (df[field] < 0).sum()
                if negative_count > 0:
                    errors.append(ValidationError(
                        field, f'Negative values in field: {field} ({negative_count} negative)', 'warning',
                        negative_count, 'All positive'
                    ))

        # Check side values
        if 'side' in df.columns:
            invalid_sides = df[~df['side'].isin(['buy', 'sell'])]
            if not invalid_sides.empty:
                errors.append(ValidationError(
                    'side', f'Invalid side values: {invalid_sides["side"].unique()}', 'error',
                    invalid_sides["side"].unique(), "['buy', 'sell']"
                ))

        # Calculate accuracy score
        total_checks = len(numeric_fields) + len(positive_fields) + 1  # +1 for side validation
        passed_checks = total_checks - len([e for e in errors if e.severity == 'error'])
        accuracy = passed_checks / total_checks if total_checks > 0 else 0

        return accuracy, errors

    def _check_ticker_accuracy(self, data: Dict) -> Tuple[float, List[ValidationError]]:
        """Check ticker data accuracy."""
        errors = []

        # Check numeric fields
        numeric_fields = self.ticker_rules.get('numeric_fields', [])
        for field in numeric_fields:
            if field in data:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    errors.append(ValidationError(
                        field, f'Non-numeric value in field: {field}', 'error', data[field], 'numeric'
                    ))

        # Check positive fields
        positive_fields = self.ticker_rules.get('positive_fields', [])
        for field in positive_fields:
            if field in data:
                try:
                    value = float(data[field])
                    if value < 0:
                        errors.append(ValidationError(
                            field, f'Negative value in field: {field}', 'warning', value, 'positive'
                        ))
                except (ValueError, TypeError):
                    pass

        # Check bid-ask order
        if 'bid' in data and 'ask' in data:
            try:
                bid = float(data['bid'])
                ask = float(data['ask'])
                if bid > ask:
                    errors.append(ValidationError(
                        'spread', f'Invalid bid-ask spread: bid={bid}, ask={ask}', 'error',
                        (bid, ask), 'bid <= ask'
                    ))
            except (ValueError, TypeError):
                pass

        # Calculate accuracy score
        total_checks = len(numeric_fields) + len(positive_fields) + 1  # +1 for bid-ask check
        passed_checks = total_checks - len([e for e in errors if e.severity == 'error'])
        accuracy = passed_checks / total_checks if total_checks > 0 else 0

        return accuracy, errors

    def _check_timeliness(self, df: pd.DataFrame, timestamp_field: str) -> Tuple[float, List[ValidationError]]:
        """Check data timeliness for DataFrame."""
        errors = []

        if timestamp_field not in df.columns:
            return 0, [ValidationError(
                timestamp_field, f'Missing timestamp field: {timestamp_field}', 'error', None, 'Field present'
            )]

        try:
            timestamps = pd.to_datetime(df[timestamp_field], unit='ms')
            now = pd.Timestamp.now()

            # Check for future timestamps
            future_timestamps = timestamps[timestamps > now]
            if not future_timestamps.empty:
                errors.append(ValidationError(
                    timestamp_field, f'Future timestamps found: {len(future_timestamps)} records', 'warning',
                    len(future_timestamps), 'No future timestamps'
                ))

            # Check data freshness (within last hour)
            hour_ago = now - pd.Timedelta(hours=1)
            stale_data = timestamps[timestamps < hour_ago]
            if not stale_data.empty:
                errors.append(ValidationError(
                    timestamp_field, f'Stale data found: {len(stale_data)} records older than 1 hour', 'warning',
                    len(stale_data), 'Recent data'
                ))

            # Calculate timeliness score
            total_records = len(df)
            if total_records > 0:
                timely_records = total_records - len(future_timestamps)
                timeliness = timely_records / total_records
            else:
                timeliness = 0

        except Exception as e:
            errors.append(ValidationError(
                timestamp_field, f'Error processing timestamps: {str(e)}', 'error', None, 'Valid timestamps'
            ))
            timeliness = 0

        return timeliness, errors

    def _check_dict_timeliness(self, data: Dict, timestamp_field: str) -> Tuple[float, List[ValidationError]]:
        """Check data timeliness for dictionary."""
        errors = []

        if timestamp_field not in data:
            return 0, [ValidationError(
                timestamp_field, f'Missing timestamp field: {timestamp_field}', 'error', None, 'Field present'
            )]

        try:
            timestamp = pd.to_datetime(data[timestamp_field], unit='ms')
            now = pd.Timestamp.now()

            # Check for future timestamp
            if timestamp > now:
                errors.append(ValidationError(
                    timestamp_field, f'Future timestamp: {timestamp}', 'warning', timestamp, 'Past timestamp'
                ))
                timeliness = 0.5
            else:
                # Check data freshness (within last hour)
                hour_ago = now - pd.Timedelta(hours=1)
                if timestamp < hour_ago:
                    errors.append(ValidationError(
                        timestamp_field, f'Stale data: timestamp is older than 1 hour', 'warning', timestamp, 'Recent data'
                    ))
                    timeliness = 0.7
                else:
                    timeliness = 1.0

        except Exception as e:
            errors.append(ValidationError(
                timestamp_field, f'Error processing timestamp: {str(e)}', 'error', data[timestamp_field], 'Valid timestamp'
            ))
            timeliness = 0

        return timeliness, errors

    def _determine_result(self, overall_score: float, errors: List[ValidationError]) -> DataValidationResult:
        """Determine validation result based on score and errors."""
        # Check for critical errors
        critical_errors = [e for e in errors if e.severity == 'error']
        if critical_errors:
            return DataValidationResult.INVALID

        # Check overall score
        if overall_score >= self.accuracy_threshold:
            return DataValidationResult.VALID
        elif overall_score >= self.completeness_threshold:
            return DataValidationResult.WARNING
        else:
            return DataValidationResult.INVALID

    def _create_report(self, data_type: str, exchange: str, symbol: str, result: DataValidationResult,
                      errors: List[ValidationError], accuracy_score: float, completeness_score: float,
                      timeliness_score: float, overall_score: float) -> ValidationReport:
        """Create validation report."""
        return ValidationReport(
            data_type=data_type,
            exchange=exchange,
            symbol=symbol,
            timestamp=datetime.now(),
            result=result,
            errors=errors,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            timeliness_score=timeliness_score,
            overall_score=overall_score
        )