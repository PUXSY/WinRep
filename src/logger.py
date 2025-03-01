import logging
from pathlib import Path
from datetime import datetime

base_dir = Path(__file__).parent / "../logs"
if not base_dir.exists() and base_dir.is_dir():
    print("Not a valid directory path for logs. Using default path.")
    base_dir = Path("./../logs")

class Logger:
    """A class to handle error and info logging with proper file handling and timestamps."""
    
    def __init__(self, log_dir: str = base_dir):
        """
        Initialize the logger with a directory for storing log files.
        
        Args:
            log_dir: Directory path where log files will be stored. Defaults to './../logs'.
        """
        self.path_to_log_dir = Path(log_dir)
        self._setup_log_directory()
        
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.log_file_path = self.path_to_log_dir / f"{self.timestamp}.log"
        
        # Setup or reuse existing logger
        self.logger = self._get_or_create_logger()
        
    def _get_or_create_logger(self) -> logging.Logger:
        """
        Get an existing logger or create a new one if none exists.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger_name = f"WinRepLogger_{self.timestamp}"
        logger = logging.getLogger(logger_name)
        
        # Only configure if handlers haven't been added already
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            
            # Create file handler
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_log_directory(self) -> None:
        """Create logs directory if it doesn't exist."""
        try:
            self.path_to_log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise OSError(f"Failed to create log directory due to permission error: {e}")
        except Exception as e:
            raise OSError(f"Failed to create log directory: {e}")
    
    def __enter__(self):
        """Context manager entry point."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point - ensures proper cleanup.
        
        Args:
            exc_type: Type of exception
            exc_val: Exception value
            exc_tb: Exception traceback
        
        Returns:
            bool: Whether to suppress exceptions
        """
        # Close all handlers
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        
        if exc_type is not None:
            return False  # Re-raise any exceptions
        return True
    
    def log_error(self, error_message: str) -> None:
        """
        Log an error message with timestamp.
        
        Args:
            error_message: The error message to log
        """
        try:
            self.logger.error(error_message)
        except Exception as e:
            print(f"Failed to log error: {e}")
            print(f"Original error: {error_message}")
    
    def log_info(self, message: str) -> None:
        """
        Log an informational message with timestamp.
        
        Args:
            message: The message to log
        """
        try:
            self.logger.info(message)
        except Exception as e:
            print(f"Failed to log message: {e}")
            print(f"Original message: {message}")
    
    def log_warning(self, message: str) -> None:
        """
        Log a warning message with timestamp.
        
        Args:
            message: The warning message to log
        """
        try:
            self.logger.warning(message)
        except Exception as e:
            print(f"Failed to log warning: {e}")
            print(f"Original warning: {message}")
    
    def log_and_print(self, message: str, level: str = "info") -> None:
        """
        Log a message and print it to console.
        
        Args:
            message: The message to log and print
            level: The logging level ('info', 'warning', or 'error')
        """
        print(message)
        if level.lower() == "info":
            self.log_info(message)
        elif level.lower() == "warning":
            self.log_warning(message)
        elif level.lower() == "error":
            self.log_error(message)
    
    @property
    def log_file(self) -> Path:
        """Return the current log file path."""
        return self.log_file_path