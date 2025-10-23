# MySQL to PostgreSQL Conversion Guide

A Python script to convert MySQL dump files to PostgreSQL format, compatible with Supabase and other PostgreSQL databases.

## 🎯 Purpose

This tool automatically converts MySQL database dumps (created with `mysqldump`) into PostgreSQL-compatible SQL files, handling all the syntax differences and compatibility issues between the two database systems.

## 📋 Requirements

- Python 3.x
- A MySQL dump file (`.sql`)

No additional Python packages required - uses only standard library modules.

## 🚀 Quick Start

### Basic Usage

```bash
# Convert with default output name (adds _postgres suffix)
python3 mysql_to_pgsql.py Dump20251023.sql

# Specify custom output file
python3 mysql_to_pgsql.py input.sql output_postgres.sql
```

### Default Behavior

If you run the script without arguments, it looks for `Dump20251023.sql` and outputs to `Dump20251023_postgres.sql`:

```bash
python3 mysql_to_pgsql.py
```

## 🔄 What Gets Converted

### Data Types

| MySQL Type | PostgreSQL Type |
|------------|----------------|
| `int` | `INTEGER` |
| `AUTO_INCREMENT` | `SERIAL` |
| `double` | `DOUBLE PRECISION` |
| `tinyint(1)` | `BOOLEAN` |
| `tinyint` | `SMALLINT` |
| `datetime` | `TIMESTAMP` |
| `longtext` | `TEXT` |
| `mediumtext` | `TEXT` |

### Syntax Changes

#### 1. **Identifiers**
- MySQL backticks: `` `table_name` `` → PostgreSQL double quotes: `"table_name"`

#### 2. **String Escaping**
- MySQL style: `\'` → PostgreSQL style: `''`
- Example: `'It\'s working'` → `'It''s working'`

#### 3. **Timestamps**
- `CURRENT_TIMESTAMP` → `NOW()`
- Removes `ON UPDATE CURRENT_TIMESTAMP` (handle with triggers if needed)

#### 4. **Character Sets & Collations**
- Removes `CHARACTER SET utf8mb4`
- Removes `COLLATE utf8mb4_0900_ai_ci`
- Applies to both table-level and column-level definitions

#### 5. **Table Options**
- Removes `ENGINE=InnoDB`
- Removes `AUTO_INCREMENT=n`
- Removes MySQL-specific comments (e.g., `/*!40101 ... */`)

#### 6. **Table Operations**
- Removes `LOCK TABLES` / `UNLOCK TABLES`
- Removes `ALTER TABLE ... DISABLE KEYS` / `ENABLE KEYS`
- Removes regular `KEY` definitions (non-foreign, non-primary keys)

#### 7. **Foreign Keys**
- **Critical Feature**: Extracts all foreign key constraints from table definitions
- Moves them to the end of the file as `ALTER TABLE` statements
- Prevents dependency errors during import
- Example:
  ```sql
  -- In CREATE TABLE (removed):
  CONSTRAINT "fk_name" FOREIGN KEY ("col") REFERENCES "other_table" ("id")
  
  -- At end of file (added):
  ALTER TABLE "table" ADD CONSTRAINT "fk_name" FOREIGN KEY ("col") REFERENCES "other_table" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
  ```

## 📁 Output Structure

The converted PostgreSQL file has this structure:

```sql
-- Header with PostgreSQL settings
SET statement_timeout = 0;
SET client_encoding = 'UTF8';
...

-- All CREATE TABLE statements (without foreign keys)
DROP TABLE IF EXISTS "table1";
CREATE TABLE "table1" (...);

-- All INSERT statements with data
INSERT INTO "table1" VALUES (...);

-- Foreign key constraints at the end
ALTER TABLE "table1" ADD CONSTRAINT "fk1" FOREIGN KEY ...;
ALTER TABLE "table2" ADD CONSTRAINT "fk2" FOREIGN KEY ...;
```

## 🎯 Importing into Supabase

### Method 1: SQL Editor (Recommended)

1. Open your Supabase project
2. Go to **SQL Editor** in the sidebar
3. Create a new query
4. Copy and paste the entire contents of `*_postgres.sql`
5. Click **Run** or press `Ctrl+Enter`

### Method 2: Command Line (psql)

```bash
# Get your connection details from Supabase dashboard
psql -h db.<your-project-ref>.supabase.co \
     -U postgres \
     -d postgres \
     -f Dump20251023_postgres.sql
```

You'll be prompted for your database password (found in Supabase Settings → Database).

### Method 3: Using Supabase CLI

```bash
supabase db reset --db-url "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres" < Dump20251023_postgres.sql
```

## 🔧 Troubleshooting

### Common Errors and Solutions

#### Error: `syntax error at or near "CHARACTER"`
**Cause**: Column-level `CHARACTER SET` or `COLLATE` not removed  
**Solution**: Script now handles this - re-run the conversion

#### Error: `relation "table_name" does not exist`
**Cause**: Foreign key references a table that hasn't been created yet  
**Solution**: Script now moves all foreign keys to the end - re-run the conversion

#### Error: `type "double" does not exist`
**Cause**: MySQL `double` type not converted  
**Solution**: Script now converts to `DOUBLE PRECISION` - re-run the conversion

#### Error: `syntax error at or near "undefined"`
**Cause**: Incorrectly escaped quotes in strings  
**Solution**: Script now converts `\'` to `''` - re-run the conversion

#### Error: Trailing comma before `)`
**Cause**: Leftover comma after removing constraints  
**Solution**: Script now cleans up trailing commas - re-run the conversion

### Manual Adjustments

After conversion, you may need to manually adjust:

1. **Sequences**: If you need to reset auto-increment values:
   ```sql
   SELECT setval('"table_name_id_seq"', (SELECT MAX(id) FROM "table_name"));
   ```

2. **Indexes**: Regular indexes (non-foreign key) are removed. Add them back if needed:
   ```sql
   CREATE INDEX idx_name ON "table_name" ("column_name");
   ```

3. **Triggers**: `ON UPDATE CURRENT_TIMESTAMP` is removed. Create trigger if needed:
   ```sql
   CREATE OR REPLACE FUNCTION update_modified_column()
   RETURNS TRIGGER AS $$
   BEGIN
       NEW.updated_at = NOW();
       RETURN NEW;
   END;
   $$ language 'plpgsql';
   
   CREATE TRIGGER update_table_modtime
   BEFORE UPDATE ON "table_name"
   FOR EACH ROW
   EXECUTE FUNCTION update_modified_column();
   ```

## 📊 Example Conversion

### Before (MySQL):
```sql
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `balance` double DEFAULT '0',
  `active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  CONSTRAINT `users_assoc_fk` FOREIGN KEY (`association_id`) REFERENCES `associations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=100 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `users` VALUES (1,'John O\'Connor',100.50,1,'2025-01-01 00:00:00');
```

### After (PostgreSQL):
```sql
CREATE TABLE "users" (
  "id" SERIAL,
  "name" VARCHAR(100) NOT NULL,
  "balance" DOUBLE PRECISION DEFAULT '0',
  "active" BOOLEAN DEFAULT '1',
  "created_at" TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY ("id")
);

INSERT INTO "users" VALUES (1,'John O''Connor',100.50,1,'2025-01-01 00:00:00');

-- Foreign key constraints (added after table creation)
ALTER TABLE "users" ADD CONSTRAINT "users_assoc_fk" FOREIGN KEY ("association_id") REFERENCES "associations" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
```

## ⚙️ Script Features

### Smart Foreign Key Handling
- Automatically detects all foreign key constraints
- Extracts them from `CREATE TABLE` statements
- Adds them at the end using `ALTER TABLE`
- Preserves all constraint options (`ON DELETE CASCADE`, etc.)

### Comprehensive Type Conversion
- Handles all common MySQL data types
- Preserves column attributes (NOT NULL, DEFAULT, etc.)
- Converts default values appropriately

### Clean Output
- Removes MySQL-specific comments
- Cleans up trailing commas
- Adds PostgreSQL-compatible header
- Maintains readability with proper formatting

## 🐛 Known Limitations

1. **Custom Functions**: MySQL custom functions need manual conversion
2. **Stored Procedures**: Not automatically converted
3. **Views**: May need adjustment
4. **Full-text Indexes**: Removed (use PostgreSQL's full-text search)
5. **Spatial Data**: May need manual conversion
6. **Triggers**: Need to be recreated manually

## 📝 Best Practices

1. **Always review the output** before importing
2. **Test on a development database** first
3. **Backup your target database** before importing
4. **Check foreign key relationships** after import
5. **Verify data integrity** with row counts:
   ```sql
   SELECT COUNT(*) FROM "table_name";
   ```

## 🤝 Contributing

Found an issue or want to improve the converter? The script is designed to be easily extensible. Key areas:

- **Line 23-34**: Quote escaping in INSERT statements
- **Line 67-83**: Data type conversions
- **Line 117-140**: Foreign key extraction
- **Line 157**: Trailing comma cleanup

## 📄 License

Free to use and modify for your needs.

## 🆘 Support

If you encounter issues:

1. Check the "Troubleshooting" section above
2. Review the error message carefully
3. Check the output file around the line number mentioned in the error
4. Re-run the conversion script (it's been updated to fix common issues)

## ✨ Success Checklist

After running the conversion and importing:

- [ ] All tables created successfully
- [ ] Data imported without errors
- [ ] Foreign keys applied correctly
- [ ] Row counts match source database
- [ ] Application can connect and query data
- [ ] No unexpected NULL values
- [ ] Timestamps preserved correctly
- [ ] Decimal/float values accurate

---

**Happy Converting! 🎉**

For Supabase-specific questions, visit: https://supabase.com/docs

