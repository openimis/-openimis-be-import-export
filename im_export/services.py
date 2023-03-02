import logging
from typing import Tuple, Any, Dict, List
from tablib import Dataset

from im_export.resources import InsureeResource

logger = logging.getLogger(__name__)


class InsureeImportExportService:
    supported_content_types = {
        'xls': 'application/vnd.ms-excel',
        'csv': 'text/csv',
        'json': 'application/json',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }

    class Strategy:
        INSERT = 'insert'

    supported_strategies = (Strategy.INSERT,)

    def __init__(self, user):
        self._user = user
        self._resource = InsureeResource(user)

    def export_insurees(self, export_format: str = 'csv') -> Tuple[str, Any]:
        '''
        @param export_format: export format, must be one of the keys of supported_content_types
        @return: Tuple of content type for a given format and the export in given format
        '''
        if export_format not in self.supported_content_types:
            raise ValueError(f'Non-supported export format: {export_format}')

        # All supported formats match Tablib attrs, to update if that's not valid anymore
        return self.supported_content_types[export_format], \
            getattr(self._resource.export(), export_format)

    def import_insurees(self, import_file, dry_run: bool = False, strategy: str = Strategy.INSERT) \
            -> Tuple[bool, Dict[str, int], List[str]]:
        if not import_file:
            raise ValueError(f'Missing import file')
        if strategy not in self.supported_strategies:
            raise ValueError(f'Non-supported strategy: {strategy}')

        try:
            data_set = Dataset(headers=InsureeResource.insuree_headers).load(import_file.read().decode())
        except Exception as e:
            raise ValueError('Failed to parse input file') from e

        data_set = self._resource.validate_and_sort_dataset(data_set)

        dry_run_result = self._resource.import_data(data_set, dry_run=True)  # Test the data import
        totals = self._get_totals_from_result(dry_run_result)
        errors = self._get_errors_from_result(dry_run_result)
        success = not dry_run_result.has_errors() and not dry_run_result.has_validation_errors()

        if not dry_run:
            if success:
                self._resource.import_data(data_set, dry_run=False)  # Actually import
                logger.info(f'Imported {totals["sent"]} insurees')
            else:
                logger.info(f'Failed to import {totals["sent"]} insurees, details: {totals}, errors: {errors}')

        return success, totals, errors

    @staticmethod
    def _get_totals_from_result(result):
        return {
            'sent': result.total_rows,
            'created': result.totals['new'],
            'updated': result.totals['update'],
            'deleted': result.totals['delete'],
            'skipped': result.totals['skip'],
            'invalid': result.totals['invalid'],
            'failed': result.totals['error']
        }

    @staticmethod
    def _get_errors_from_result(result):
        errors = []
        if result.has_validation_errors():
            for invalid_row in result.invalid_rows:
                errors.append(f"row ({invalid_row.number}) - {invalid_row.error.message}")
        if result.has_errors():
            for index, row_error in result.row_errors():
                for error in row_error:
                    errors.append(f"row ({index}) - {error.error}")
        return errors
