#From db import Database class
from db import Database
from worker import Worker
if __name__ == '__main__':
    db = Database()
    user = Worker(db, 'ng@snu.edu.in')
    print(user.name)
    
    pass