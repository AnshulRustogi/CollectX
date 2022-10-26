#From db import Database class
from db import Database
from worker import Worker
if __name__ == '__main__':
    db = Database()
    db.add_remove_mcd("ar794@snu.edu.in", "M", True)
    db.add_remove_mcd("m2@snu.edu.in", "M", True)
    db.add_remove_mcd("m3@snu.edu.in", "M", True)
    
    db.add_remove_mcd("w1@snu.edu.in", "W", True)
    db.add_remove_mcd("w2@snu.edu.in", "W", True)
    db.add_remove_mcd("w3@snu.edu.in", "W", True)
    db.add_remove_mcd("w4@snu.edu.in", "W", True)

    #Add manager to Person table
    db.cursor.execute("INSERT INTO Person VALUES ('Anshul Rustogi', 'ar794@snu.edu.in', 9821672309, 'M')," +
    "('M2', 'M2@snu.edu.in', 9876543210, 'M')," +
    "('M3', 'M3@snu.edu.in', 9876543210, 'M')," +
    "('W1', 'w1@snu.edu.in', 9876543210, 'W')," +
    "('W2', 'w2@snu.edu.in', 9876543210, 'W')")

    db.add_remove_worker("ar794@snu.edu.in", "Full Name", "w1@snu.edu.in", 0, "w", False)
    db.add_remove_worker("ar794@snu.edu.in", "Full Name", "w3@snu.edu.in", 0, "w", True)
    db.add_remove_worker("m2@snu.edu.in", "Full Name", "w2@snu.edu.in", 0, "w", False)
    db.add_remove_worker("m3@snu.edu.in", "Full Name", "w4@snu.edu.in", 0, "w", True)
    
