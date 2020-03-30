"""Migration for a given Submitty course database."""


def up(config, database, semester, course):
    """
    Run up migration.

    :param config: Object holding configuration details about Submitty
    :type config: migrator.config.Config
    :param database: Object for interacting with given database for environment
    :type database: migrator.db.Database
    :param semester: Semester of the course being migrated
    :type semester: str
    :param course: Code of course being migrated
    :type course: str
    """
    # make a new column with time zones
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_in_temp timestamp with time zone;");
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_help_start_temp timestamp with time zone;");
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_out_temp timestamp with time zone;");
    # copy over old data to new column with timezone
    database.execute("UPDATE queue SET time_in_temp = time_in;");
    database.execute("UPDATE queue SET time_help_start_temp = time_help_start;");
    database.execute("UPDATE queue SET time_out_temp = time_out;");
    # drop old data
    database.execute("ALTER TABLE queue DROP COLUMN time_in; ");
    database.execute("ALTER TABLE queue DROP COLUMN time_help_start; ");
    database.execute("ALTER TABLE queue DROP COLUMN time_out; ");
    # rename new columns to be the same name as the old ones but now have timezones
    database.execute("ALTER TABLE queue RENAME COLUMN time_in_temp TO time_in;");
    database.execute("ALTER TABLE queue RENAME COLUMN time_help_start_temp TO time_help_start;");
    database.execute("ALTER TABLE queue RENAME COLUMN time_out_temp TO time_out;");


def down(config, database, semester, course):
    """
    Run down migration (rollback).

    :param config: Object holding configuration details about Submitty
    :type config: migrator.config.Config
    :param database: Object for interacting with given database for environment
    :type database: migrator.db.Database
    :param semester: Semester of the course being migrated
    :type semester: str
    :param course: Code of course being migrated
    :type course: str
    """
    # make a new column without time zones
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_in_temp timestamp;");
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_help_start_temp timestamp;");
    database.execute("ALTER TABLE queue add IF NOT EXISTS time_out_temp timestamp;");
    # copy over old data to new column without timezone
    database.execute("UPDATE queue SET time_in_temp = time_in;");
    database.execute("UPDATE queue SET time_help_start_temp = time_help_start;");
    database.execute("UPDATE queue SET time_out_temp = time_out;");
    # drop old data
    database.execute("ALTER TABLE queue DROP COLUMN time_in; ");
    database.execute("ALTER TABLE queue DROP COLUMN time_help_start; ");
    database.execute("ALTER TABLE queue DROP COLUMN time_out; ");
    # rename new columns to be the same name as the old ones but now have no timezones
    database.execute("ALTER TABLE queue RENAME COLUMN time_in_temp TO time_in;");
    database.execute("ALTER TABLE queue RENAME COLUMN time_help_start_temp TO time_help_start;");
    database.execute("ALTER TABLE queue RENAME COLUMN time_out_temp TO time_out;");
