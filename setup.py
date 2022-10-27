#From db import Database class
from db import Database
from worker import Worker
if __name__ == '__main__':
    db = Database()
    #db.add_remove_mcd("ar794@snu.edu.in", "M", True)
    #db.add_remove_mcd("m2@snu.edu.in", "M", True)
    #db.add_remove_mcd("m3@snu.edu.in", "M", True)
    
    #db.add_remove_mcd("w1@snu.edu.in", "W", True)
    #db.add_remove_mcd("w2@snu.edu.in", "W", True)
    #db.add_remove_mcd("w3@snu.edu.in", "W", True)
    #db.add_remove_mcd("w4@snu.edu.in", "W", True)

    #Add manager to Person table
    db.cursor.execute("INSERT INTO Person VALUES ('Anshul Rustogi', 'ar794@snu.edu.in', 9821672309, 'M')," +
    "('M2', 'M2@snu.edu.in', 9876543210, 'M')," +
    "('M3', 'M3@snu.edu.in', 9876543210, 'M')," +
    "('W1', 'w1@snu.edu.in', 9876543210, 'W')," +
    "('W2', 'w2@snu.edu.in', 9876543210, 'W')," +
    "('Paritosh Dutta', 'pd794@snu.edu.in', 0, 'M');")

    db.add_remove_worker("ar794@snu.edu.in", "Full Name", "w1@snu.edu.in", 0, "w", False)
    db.add_remove_worker("ar794@snu.edu.in", "Full Name", "w3@snu.edu.in", 0, "w", True)
    db.add_remove_worker("pd794@snu.edu.in", "Full Name", "w2@snu.edu.in", 0, "w", False)
    db.add_remove_worker("pd794@snu.edu.in", "Full Name", "w4@snu.edu.in", 0, "w", True)

    db.insert_bin(0, 'Dwarka Sector 22', '','')
    db.insert_bin(1, 'Dwarka Sector 7', '', '')
    db.insert_bin(2, 'Janakpuri', '', '')
    db.insert_bin(3, 'Tilak Nagar', '', '')
    db.insert_bin(4, 'Subhash Nagar', '', '')
    db.insert_bin(5, 'Kirti Nagar', '', '')
    db.insert_bin(6, 'Tagore Garden', '', '')
    db.insert_bin(7, 'Rajouri Garden', '', '')
    db.insert_bin(8, 'Hari Nagar', '', '')
    db.insert_bin(9, 'Ashok Nagar', '', '')
    db.insert_bin(10, 'Janakpuri', '', '')
    db.insert_bin(11, 'Nawada', '', '')
    db.insert_bin(12, 'Raj Nagar', '', '')
    db.insert_bin(13, 'Rajouri Garden', '', '')

    db.insert_edge(0, 1, 4)
    db.insert_edge(1, 2, 6.5)
    db.insert_edge(2, 3, 3)
    db.insert_edge(3, 4, 4)
    db.insert_edge(4, 5, 3.5)
    db.insert_edge(5, 6, 4.5)
    db.insert_edge(6, 7, 3)
    db.insert_edge(8, 9, 2)
    db.insert_edge(2, 8, 2.5)
    db.insert_edge(1, 11, 7)
    db.insert_edge(11, 2, 6.5)
    db.insert_edge(8, 3, 3.5)
    db.insert_edge(3, 9, 2)
    db.insert_edge(9, 4, 2)
    db.insert_edge(1, 12, 1.5)
    db.insert_edge(12, 0, 3.5)
    

    
