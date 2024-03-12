from enum import Enum

class MessageTypes(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    INFO = 'info'
    WARNING = 'warning'
    FORM_ERROR = 'form_error'
    
class OnlineTransactionStatus(Enum):
    SUCCESSFUL = 'successful'
    FAILED = 'failed'