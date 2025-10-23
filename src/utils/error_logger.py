import logging
import os
from datetime import datetime
import traceback

class ErrorLogger:
    def __init__(self, log_dir="logs"):
        """에러 로그를 파일에 저장하는 클래스"""
        self.log_dir = log_dir
        self.ensure_log_dir()
        self.setup_logger()
    
    def ensure_log_dir(self):
        """로그 디렉토리가 없으면 생성"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logger(self):
        """로거 설정"""
        log_filename = f"{self.log_dir}/streamlit_errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # 콘솔에도 출력
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error_msg, error_type="ERROR", additional_info=None):
        """에러를 로그 파일에 저장"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] {error_type}: {error_msg}"
        if additional_info:
            log_entry += f"\n추가 정보: {additional_info}"
        
        self.logger.error(log_entry)
        
        # 로그 파일 경로 반환
        log_filename = f"{self.log_dir}/streamlit_errors_{datetime.now().strftime('%Y%m%d')}.log"
        return log_filename
    
    def log_exception(self, exception, context=None):
        """예외 정보를 상세히 로그에 저장"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        error_msg = f"[{timestamp}] EXCEPTION: {str(exception)}"
        if context:
            error_msg += f"\n컨텍스트: {context}"
        
        error_msg += f"\n스택 트레이스:\n{traceback.format_exc()}"
        
        self.logger.error(error_msg)
        
        # 로그 파일 경로 반환
        log_filename = f"{self.log_dir}/streamlit_errors_{datetime.now().strftime('%Y%m%d')}.log"
        return log_filename

# 전역 에러 로거 인스턴스
error_logger = ErrorLogger()
