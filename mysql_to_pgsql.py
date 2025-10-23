#!/usr/bin/env python3
"""
MySQL to PostgreSQL Dump Converter
Converts a MySQL dump file to PostgreSQL format for importing into Supabase
"""

import re
import sys

def convert_mysql_to_postgres(input_file, output_file):
    """Convert MySQL dump to PostgreSQL dump"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove MySQL-specific comments
    content = re.sub(r'/\*![\d\s]*.*?\*/;?', '', content, flags=re.DOTALL)
    
    # Remove MySQL SET commands at the beginning
    content = re.sub(r'SET @OLD_.*?;', '', content)
    content = re.sub(r'SET @saved_.*?;', '', content)
    
    # Fix MySQL escaped quotes: \' -> '' (PostgreSQL style)
    # This needs to be done carefully to handle strings properly
    # Replace \' with '' but only in data values (not in comments)
    def fix_quotes_in_inserts(match):
        """Replace MySQL-style escaped quotes with PostgreSQL style in INSERT statements"""
        insert_stmt = match.group(0)
        # Replace \' with '' in the INSERT statement
        insert_stmt = insert_stmt.replace("\\'", "''")
        return insert_stmt
    
    # Apply the fix to INSERT statements
    content = re.sub(r'INSERT INTO.*?;', fix_quotes_in_inserts, content, flags=re.DOTALL)
    
    # Remove LOCK TABLES and UNLOCK TABLES
    content = re.sub(r'LOCK TABLES `.*?` WRITE;', '', content)
    content = re.sub(r'UNLOCK TABLES;', '', content)
    
    # Replace backticks with double quotes for identifiers
    content = content.replace('`', '"')
    
    # Replace ENGINE=InnoDB and similar
    content = re.sub(r'\s*ENGINE\s*=\s*\w+', '', content, flags=re.IGNORECASE)
    
    # Replace DEFAULT CHARSET and COLLATE (table-level)
    content = re.sub(r'\s*DEFAULT CHARSET\s*=\s*\w+', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\s*COLLATE\s*=\s*\w+', '', content, flags=re.IGNORECASE)
    
    # Remove CHARACTER SET and COLLATE from column definitions
    content = re.sub(r'\s+CHARACTER SET\s+\w+', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\s+COLLATE\s+\w+', '', content, flags=re.IGNORECASE)
    
    # Replace AUTO_INCREMENT with GENERATED ALWAYS AS IDENTITY
    # First, handle AUTO_INCREMENT in table options (at the end of CREATE TABLE)
    content = re.sub(r'\s*AUTO_INCREMENT\s*=\s*\d+', '', content, flags=re.IGNORECASE)
    
    # Handle AUTO_INCREMENT in column definitions
    # Pattern: "id" int NOT NULL AUTO_INCREMENT,
    content = re.sub(
        r'("?\w+"?)\s+(int|bigint|smallint)\s+NOT\s+NULL\s+AUTO_INCREMENT',
        r'\1 SERIAL',
        content,
        flags=re.IGNORECASE
    )
    
    # Replace int with INTEGER (more standard in PostgreSQL)
    content = re.sub(r'\b(int)\b(?!\s+SERIAL)', 'INTEGER', content, flags=re.IGNORECASE)
    
    # Replace double with DOUBLE PRECISION
    content = re.sub(r'\bdouble\b', 'DOUBLE PRECISION', content, flags=re.IGNORECASE)
    
    # Replace float with REAL (or keep as is, both work in PostgreSQL)
    # content = re.sub(r'\bfloat\b', 'REAL', content, flags=re.IGNORECASE)
    
    # Replace tinyint(1) with BOOLEAN
    content = re.sub(r'tinyint\(1\)', 'BOOLEAN', content, flags=re.IGNORECASE)
    
    # Replace tinyint with SMALLINT
    content = re.sub(r'tinyint(\(\d+\))?', 'SMALLINT', content, flags=re.IGNORECASE)
    
    # Replace datetime with TIMESTAMP
    content = re.sub(r'\bdatetime\b', 'TIMESTAMP', content, flags=re.IGNORECASE)
    
    # Replace varchar to be case-consistent
    content = re.sub(r'\bvarchar\b', 'VARCHAR', content, flags=re.IGNORECASE)
    
    # Replace text types
    content = re.sub(r'\blongtext\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\bmediumtext\b', 'TEXT', content, flags=re.IGNORECASE)
    
    # Fix timestamp defaults with ON UPDATE
    # MySQL: timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    # PostgreSQL: timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP (remove ON UPDATE, handle with trigger if needed)
    content = re.sub(
        r'(TIMESTAMP\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP)\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP',
        r'\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Replace CURRENT_TIMESTAMP with NOW() for consistency
    content = re.sub(r'\bCURRENT_TIMESTAMP\b', 'NOW()', content, flags=re.IGNORECASE)
    
    # Handle KEY definitions and extract FOREIGN KEY constraints
    # We need to defer foreign keys to avoid dependency issues
    lines = content.split('\n')
    new_lines = []
    foreign_keys = []
    in_create_table = False
    current_table = None
    
    for line in lines:
        # Track if we're inside a CREATE TABLE statement
        if 'CREATE TABLE' in line.upper():
            in_create_table = True
            # Extract table name
            match = re.search(r'CREATE TABLE\s+"([^"]+)"', line, re.IGNORECASE)
            if match:
                current_table = match.group(1)
        
        # Extract FOREIGN KEY constraints to add later
        if in_create_table and re.search(r'CONSTRAINT\s+"[^"]+"\s+FOREIGN KEY', line, re.IGNORECASE):
            # Store the foreign key to add later
            fk_match = re.search(
                r'CONSTRAINT\s+"([^"]+)"\s+FOREIGN KEY\s+\(([^)]+)\)\s+REFERENCES\s+"([^"]+)"\s+\(([^)]+)\)(.+)',
                line,
                re.IGNORECASE
            )
            if fk_match and current_table:
                constraint_name = fk_match.group(1)
                fk_columns = fk_match.group(2)
                ref_table = fk_match.group(3)
                ref_columns = fk_match.group(4)
                actions = fk_match.group(5).rstrip(',').strip()
                
                foreign_keys.append({
                    'table': current_table,
                    'constraint': constraint_name,
                    'columns': fk_columns,
                    'ref_table': ref_table,
                    'ref_columns': ref_columns,
                    'actions': actions
                })
            # Skip this line from the CREATE TABLE
            continue
        
        # Skip KEY lines that are not FOREIGN KEY or PRIMARY KEY
        if in_create_table and re.match(r'\s*KEY\s+"', line, re.IGNORECASE):
            # Skip this line (it's a regular index, we'll handle it separately if needed)
            continue
        
        # Check if we're ending the CREATE TABLE
        if in_create_table and ')' in line and ';' in line:
            in_create_table = False
            current_table = None
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Clean up trailing commas before closing parentheses in CREATE TABLE statements
    content = re.sub(r',(\s*\n\s*\);)', r'\1', content)
    
    # Add foreign keys at the end
    if foreign_keys:
        fk_statements = ['\n\n-- Foreign key constraints (added after table creation to avoid dependency issues)\n']
        for fk in foreign_keys:
            fk_stmt = f'ALTER TABLE "{fk["table"]}" ADD CONSTRAINT "{fk["constraint"]}" FOREIGN KEY ({fk["columns"]}) REFERENCES "{fk["ref_table"]}" ({fk["ref_columns"]}) {fk["actions"]};'
            fk_statements.append(fk_stmt)
        content += '\n'.join(fk_statements)
    
    # Remove DISABLE/ENABLE KEYS
    content = re.sub(r'ALTER TABLE ".*?" DISABLE KEYS;?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'ALTER TABLE ".*?" ENABLE KEYS;?', '', content, flags=re.IGNORECASE)
    
    # Clean up multiple blank lines
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # Add PostgreSQL-specific header
    postgres_header = """-- Converted from MySQL to PostgreSQL
-- Compatible with Supabase
-- Original MySQL dump: {}

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

""".format(input_file)
    
    content = postgres_header + content
    
    # Write the converted content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Successfully converted MySQL dump to PostgreSQL format")
    print(f"📄 Input:  {input_file}")
    print(f"📄 Output: {output_file}")
    print(f"\n📋 Next steps:")
    print(f"1. Review the output file for any manual adjustments needed")
    print(f"2. Import into Supabase using: psql -h <host> -U <user> -d <database> -f {output_file}")
    print(f"   Or use the Supabase SQL Editor to paste and run the contents")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.sql', '_postgres.sql')
    else:
        # Default files
        input_file = "Dump20251023.sql"
        output_file = "Dump20251023_postgres.sql"
    
    try:
        convert_mysql_to_postgres(input_file, output_file)
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)

