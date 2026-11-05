import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReadingHistoryTest(unittest.TestCase):
    def test_generation_survives_process_restart_with_questions_and_types(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, 'WORDMASTER_DATA_DIR': directory, 'PYTHONPATH': str(ROOT / 'server')}
            article = {'title': 'A short article', 'content': 'A text.', 'questions': [
                {'type': '推理判断', 'question': 'Why?', 'options': ['A', 'B'], 'answer': 'A', 'explanation': 'Because.'},
            ]}
            save = "from reading_history import save_reading; import json; print(save_reading(json.loads(%r), 'IELTS', '中等', '科技'))" % __import__('json').dumps(article)
            subprocess.run([sys.executable, '-c', save], env=env, check=True, capture_output=True)
            read = "from reading_history import list_readings,get_reading; x=list_readings()[0]; print(x['question_types'][0], get_reading(x['id'])['questions'][0]['question'])"
            result = subprocess.run([sys.executable, '-c', read], env=env, check=True, capture_output=True, text=True)
            self.assertIn('推理判断 Why?', result.stdout)

    def test_delete_one_reading_keeps_other_records(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, 'WORDMASTER_DATA_DIR': directory, 'PYTHONPATH': str(ROOT / 'server')}
            script = (
                "from reading_history import save_reading, list_readings, get_reading, delete_reading; "
                "one=save_reading({'title':'first','questions':[]},'IELTS','中等','科技'); "
                "two=save_reading({'title':'second','questions':[]},'IELTS','中等','历史'); "
                "assert delete_reading(one); assert not delete_reading(one); "
                "assert get_reading(one) is None; "
                "assert [item['id'] for item in list_readings()]==[two]"
            )
            subprocess.run([sys.executable, '-c', script], env=env, check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
