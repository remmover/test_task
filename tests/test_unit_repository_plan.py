import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from fastapi import HTTPException

from src.repository.plan import download_plan


class TestDownloadPlan(unittest.TestCase):
    @patch("src.repository.plan.pd.read_excel")
    @patch("src.repository.plan.sessionmanager.session")
    async def test_download_plan_success(self, mock_session, mock_read_excel):
        mock_excel_file = MagicMock()
        mock_session_instance = mock_session.return_value.__aenter__.return_value
        mock_session_instance.execute.return_value.scalar.return_value = False

        excel_data = pd.DataFrame(
            {
                "category": ["збір", "видача", "збір"],
                "plane_date": ["2023-10-01", "2023-11-01", "2023-12-01"],
                "sum": [100, 200, 150],
            }
        )
        mock_read_excel.return_value = excel_data

        result = await download_plan(mock_excel_file)

        self.assertEqual(result, "Your expected success message")

        mock_session_instance.begin.assert_called_once()
        mock_session_instance.add.assert_called()
        mock_session_instance.commit.assert_called_once()

    @patch("src.repository.plan.pd.read_excel")
    @patch("src.repository.plan.sessionmanager.session")
    async def test_download_plan_existing_plan(self, mock_session, mock_read_excel):
        mock_excel_file = MagicMock()
        mock_session_instance = mock_session.return_value.__aenter__.return_value
        mock_session_instance.execute.return_value.scalar.return_value = True

        excel_data = pd.DataFrame(
            {
                "category": ["збір", "видача"],
                "plane_date": ["2023-10-01", "2023-11-01"],
                "sum": [100, 200],
            }
        )
        mock_read_excel.return_value = excel_data

        result = await download_plan(mock_excel_file)

        self.assertEqual(result, "Your expected plan already exists message")

        mock_session_instance.rollback.assert_called_once()

    @patch("src.repository.plan.pd.read_excel")
    @patch("src.repository.plan.sessionmanager.session")
    async def test_download_plan_error_uploading(self, mock_session, mock_read_excel):
        mock_excel_file = MagicMock()
        mock_session_instance = mock_session.return_value.__aenter__.return_value
        mock_session_instance.execute.side_effect = Exception("Some error")

        excel_data = pd.DataFrame(
            {
                "category": ["збір", "видача"],
                "plane_date": ["2023-10-01", "2023-11-01"],
                "sum": [100, 200],
            }
        )
        mock_read_excel.return_value = excel_data

        result = await download_plan(mock_excel_file)

        self.assertIsInstance(result, HTTPException)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.detail, "Your expected error message")

        mock_session_instance.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
