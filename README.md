# MySQL to PostgreSQL Converter

A Python script that automatically converts MySQL database dumps to PostgreSQL format, perfect for migrating to Supabase or any PostgreSQL database.

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Features

- **Zero Dependencies** - Uses only Python standard library
- **Smart Foreign Key Handling** - Automatically resolves table dependency issues
- **Comprehensive Type Conversion** - Handles all common MySQL data types
- **String Escaping** - Converts MySQL-style escaped quotes to PostgreSQL format
- **Supabase Ready** - Output is fully compatible with Supabase imports
- **Automated Cleanup** - Removes all MySQL-specific syntax and commands

## 📋 Installation

No installation needed! Just download the script:

```bash
git clone https://github.com/GiftSibiya/python-mysql-to-pgsql.git
cd python-mysql-to-pgsql
```

## 🎯 Quick Start

```bash
# Basic usage
python3 mysql_to_pgsql.py your_dump.sql output.sql

# With default names
python3 mysql_to_pgsql.py Dump20251023.sql
# Creates: Dump20251023_postgres.sql
```

## 📖 Usage

### Creating a MySQL Dump

First, create a dump from your MySQL database:

```bash
mysqldump -u username -p database_name > dump.sql
```

### Converting to PostgreSQL

```bash
python3 mysql_to_pgsql.py dump.sql dump_postgres.sql
```

### Importing to Supabase

**Option 1: SQL Editor (Recommended)**
1. Open your Supabase project
2. Navigate to SQL Editor
3. Copy/paste the converted file contents
4. Run the query

**Option 2: Command Line**
```bash
psql -h db.your-project.supabase.co -U postgres -d postgres -f dump_postgres.sql
```

## 🔄 What Gets Converted

| MySQL | PostgreSQL |
|-------|-----------|
| `` `identifier` `` | `"identifier"` |
| `INT AUTO_INCREMENT` | `SERIAL` |
| `double` | `DOUBLE PRECISION` |
| `tinyint(1)` | `BOOLEAN` |
| `datetime` | `TIMESTAMP` |
| `\'escaped\'` | `''escaped''` |
| `CURRENT_TIMESTAMP` | `NOW()` |
| `ENGINE=InnoDB` | *(removed)* |
| `CHARACTER SET utf8mb4` | *(removed)* |
| Foreign keys in CREATE | Moved to ALTER TABLE at end |

## ✨ Key Features Explained

### Foreign Key Dependency Resolution

The script automatically:
1. Extracts all foreign key constraints from CREATE TABLE statements
2. Creates tables without foreign keys first
3. Adds all foreign keys at the end using ALTER TABLE

This prevents "relation does not exist" errors during import.

**Before:**
```sql
CREATE TABLE "users" (
  "id" SERIAL,
  "association_id" INTEGER,
  CONSTRAINT "fk" FOREIGN KEY ("association_id") REFERENCES "associations" ("id")
);
```

**After:**
```sql
CREATE TABLE "users" (
  "id" SERIAL,
  "association_id" INTEGER
);

-- At end of file
ALTER TABLE "users" ADD CONSTRAINT "fk" FOREIGN KEY ("association_id") REFERENCES "associations" ("id");
```

### Smart Quote Escaping

Converts MySQL-style escaped quotes in data:

```sql
-- MySQL
'It\'s working'

-- PostgreSQL
'It''s working'
```

## 📚 Documentation

For detailed documentation, troubleshooting, and advanced usage, see [CONVERSION_GUIDE.md](CONVERSION_GUIDE.md).

## 🛠️ Requirements

- Python 3.x (no additional packages required)
- MySQL dump file (`.sql`)

## 🐛 Common Issues

| Error | Solution |
|-------|----------|
| `type "double" does not exist` | Re-run the script (fixed) |
| `relation "X" does not exist` | Re-run the script (FK handling fixed) |
| `syntax error at "CHARACTER"` | Re-run the script (charset removal fixed) |
| `syntax error at "undefined"` | Re-run the script (quote escaping fixed) |

The script has been updated to handle all these issues automatically.

## 📊 Example

**Input (MySQL):**
```sql
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 NOT NULL,
  `balance` double DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` VALUES (1,'John\'s Account',100.50);
```

**Output (PostgreSQL):**
```sql
CREATE TABLE "users" (
  "id" SERIAL,
  "name" VARCHAR(100) NOT NULL,
  "balance" DOUBLE PRECISION DEFAULT '0',
  PRIMARY KEY ("id")
);

INSERT INTO "users" VALUES (1,'John''s Account',100.50);
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

Created for seamless MySQL to PostgreSQL migrations, with special focus on Supabase compatibility.

## 📞 Support

- **Documentation**: [CONVERSION_GUIDE.md](CONVERSION_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/GiftSibiya/python-mysql-to-pgsql/issues)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)

---

**Made with ❤️ for database migrations**