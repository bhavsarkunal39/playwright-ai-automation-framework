import logging
import pytest

class ExceptionLog:
    
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
        logging.StreamHandler()
    ]
    )
    
    @staticmethod
    def exceptionLog(errorValue, keywrd, obj):
        classType = type(errorValue).__name__
        #logging.info(f"Exception classs: {classType}")

        match classType:
            case "TimeoutError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, Element not found or timed out: {obj}:\n{str(errorValue)}")
            case "FileNotFoundError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, File not found: {obj}:\n{str(errorValue)}")
            case "BrowserClosedError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, Cannot interact with closed browser:\n{str(errorValue)}")
            case "WebSocketError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, WebSocket-related issue: {obj} \n{str(errorValue)}")
            case "PageError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, JavaScript error on page: {obj}\n{str(errorValue)}")
            case "NetworkError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, Network resource load failure: {obj} \n{str(errorValue)}")
            case "DatabaseError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, Database connectivity Problem: {obj} \n{str(errorValue)}")        
            case "JSONDecodeError":
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, Invalid Response: {obj} \n{str(errorValue)}")        
            case _:
                logging.error(f"Exception in {keywrd} Keyword,\n Reason: {classType}, General Error: {obj} \n{str(errorValue)}")
        pytest.fail(f'Testcase failed, refer ERROR in Console.')