import os.path

HERE = os.path.dirname(__file__)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(HERE, 'db.sqlite')
    }
}

INSTALLED_APPS = (
    'tablemaker_orm',
    )

from secretkey import SECRET_KEY
