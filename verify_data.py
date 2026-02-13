"""Verify database data matches Excel output"""
from database import db

with db.get_cursor() as cursor:
    print('='*80)
    print('VERIFICATION: Student 1310050561 (Hasini Durga Kammala)')
    print('='*80)
    
    # 1. Users table
    print()
    print('>>> TABLE: Users')
    cursor.execute('''
        SELECT UserId, LoginId, FirstName, LastName, Gender, Grade, SchoolId
        FROM Users WITH (NOLOCK) WHERE LoginId = '1310050561'
    ''')
    row = cursor.fetchone()
    print(f'  UserId: {row[0]}')
    print(f'  LoginId (StudentId): {row[1]}')
    print(f'  FirstName: {row[2]}')
    print(f'  LastName: {row[3]}')
    print(f'  Gender: {row[4]}')
    print(f'  Grade: {row[5]}')
    print(f'  SchoolId: {row[6]}')
    user_id = row[0]
    
    # 2. School table
    print()
    print('>>> TABLE: School')
    cursor.execute('''
        SELECT Id, SchoolName, RegionID FROM School WITH (NOLOCK) WHERE Id = 188254
    ''')
    row = cursor.fetchone()
    print(f'  SchoolId: {row[0]}')
    print(f'  SchoolName: {row[1]}')
    print(f'  RegionID: {row[2]}')
    
    # 3. Region table
    print()
    print('>>> TABLE: Region')
    cursor.execute('SELECT RegionID, RegionName FROM Region WITH (NOLOCK) WHERE RegionID = 3')
    row = cursor.fetchone()
    print(f'  RegionID: {row[0]}')
    print(f'  RegionName: {row[1]}')
    
    # 4. CCTTestResults
    print()
    print('>>> TABLE: CCTTestResults (First 6 questions for this student)')
    cursor.execute('''
        SELECT 
            ROW_NUMBER() OVER (ORDER BY QuestionID) as QNum,
            QuestionID, 
            UserAnswer, 
            Credits
        FROM CCTTestResults WITH (NOLOCK) 
        WHERE ContestCreationID = 178 AND UserID = 307565
        ORDER BY QuestionID
    ''')
    rows = cursor.fetchall()
    for row in rows[:6]:
        print(f'    Q{row[0]}: QuestionID={row[1]}, UserAnswer="{row[2]}", Credits={row[3]}')
    print(f'    ... ({len(rows)} total questions)')
    
    # 5. QBankMaster for specific questions
    print()
    print('>>> TABLE: QBankMaster (Question details)')
    cursor.execute('''
        SELECT QuestionID, SubjectId, Answer, QuestionType, Level
        FROM QBankMaster WITH (NOLOCK)
        WHERE QuestionID IN (81719, 82350, 81689)
    ''')
    for row in cursor.fetchall():
        ans = row[2][:30] if row[2] else 'NULL'
        print(f'    QID={row[0]}: SubjectId={row[1]}, Answer="{ans}", Type={row[3]}, Level={row[4]}')
    
    # 6. Subject table
    print()
    print('>>> TABLE: Subject')
    cursor.execute('SELECT SubjectId, SubjectName FROM Subject WITH (NOLOCK)')
    for row in cursor.fetchall():
        print(f'    SubjectId={row[0]}: {row[1]}')
    
    # 7. Lov table for levels
    print()
    print('>>> TABLE: Lov (Level names)')
    cursor.execute('''
        SELECT LovId, LovName FROM Lov WITH (NOLOCK) 
        WHERE LovId IN (3286, 3287, 3288)
    ''')
    for row in cursor.fetchall():
        print(f'    LovId={row[0]}: {row[1]}')

print()
print('='*80)
print('COMPARE WITH EXCEL ROW 649 (Student 1310050561)')
print('='*80)
