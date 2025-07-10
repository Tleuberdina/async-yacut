MIN_LENGTH = 1
MAX_LENGTH = 16
FILE_EXTENSION = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
LENGTH_CODE = 6
RESERVED_WORDS = {'files', 'admin', 'api'}
MAX_ATTEMPTS = 10
ACCEPTABLE_VALUE = r'^[a-zA-Z0-9]{1,16}$'
MESSAGE_UNACCEPTABLE_NAME = 'Указано недопустимое имя для короткой ссылки'
MESSAGE_NAME_ALREADY_EXISTS = (
    'Предложенный вариант короткой ссылки уже существует.'
)
