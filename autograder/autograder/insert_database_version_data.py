
"""
This module is used for inserting/updating autograding information into the DB.
Generally, the site should be inserting an empty row into the DB for the autograding
submission and then this script updates said row, but should be fault-tolerant to
handle inserting the row if necessary.
"""
import json
import os

from submitty_utils import dateutils
from sqlalchemy import create_engine, Table, MetaData, bindparam, select, func

from . import CONFIG_PATH

with open(os.path.join(CONFIG_PATH, 'database.json')) as open_file:
    OPEN_JSON = json.load(open_file)
DB_HOST = OPEN_JSON['database_host']
DB_USER = OPEN_JSON['database_user']
DB_PASSWORD = OPEN_JSON['database_password']

with open(os.path.join(CONFIG_PATH, 'submitty.json')) as open_file:
    OPEN_JSON = json.load(open_file)
DATA_DIR = OPEN_JSON['submitty_data_dir']


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def insert_to_database(semester, course, gradeable_id, user_id, team_id, who_id, is_team, version):

    non_hidden_non_ec = 0
    non_hidden_ec = 0
    hidden_non_ec = 0
    hidden_ec = 0

    testcases = get_testcases(semester, course, gradeable_id)
    results = get_result_details(semester, course, gradeable_id, who_id, version)
    if len(testcases) != len(results['testcases']):
        print(f"ERROR!  mismatched # of testcases {len(testcases)} != {len(results['testcases'])}")
    for i in range(len(testcases)):
        if testcases[i]['hidden'] and testcases[i]['extra_credit']:
            hidden_ec += results['testcases'][i]['points']
        elif testcases[i]['hidden']:
            hidden_non_ec += results['testcases'][i]['points']
        elif testcases[i]['extra_credit']:
            non_hidden_ec += results['testcases'][i]['points']
        else:
            non_hidden_non_ec += results['testcases'][i]['points']
    submission_time = results['submission_time']

    db_name = f"submitty_{semester}_{course}"

    # If using a UNIX socket, have to specify a slightly different connection string
    if os.path.isdir(DB_HOST):
        conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{db_name}?host={DB_HOST}"
    else:
        conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{db_name}"

    engine = create_engine(conn_string)
    db = engine.connect()
    metadata = MetaData(bind=db)
    data_table = Table('electronic_gradeable_data', metadata, autoload=True)

    """
    The data row should have been inserted by PHP when the student uploads the submission, requiring
    us to do an update here (as the PHP also deals with the active version for us), but in case
    we're using some other method of grading, we'll insert the row and whoever called the script
    will need to handle the active version afterwards.
    """
    if is_team is True:
        result = db.execute(select([func.count()]).select_from(data_table)
                            .where(data_table.c.g_id == bindparam('g_id'))
                            .where(data_table.c.team_id == bindparam('team_id'))
                            .where(data_table.c.g_version == bindparam('g_version')),
                            g_id=gradeable_id,  team_id=team_id, g_version=version)
        row = result.fetchone()
        result.close()
        query_type = data_table.insert()
        if row[0] > 0:
            query_type = data_table\
                .update(
                    values={
                        data_table.c.autograding_non_hidden_non_extra_credit:
                            bindparam("autograding_non_hidden_non_extra_credit"),
                        data_table.c.autograding_non_hidden_extra_credit:
                            bindparam("autograding_non_hidden_extra_credit"),
                        data_table.c.autograding_hidden_non_extra_credit:
                            bindparam("autograding_hidden_non_extra_credit"),
                        data_table.c.autograding_hidden_extra_credit:
                            bindparam("autograding_hidden_extra_credit"),
                        data_table.c.autograding_complete:
                            bindparam("autograding_complete")
                    })\
                .where(data_table.c.g_id == bindparam('u_g_id'))\
                .where(data_table.c.team_id == bindparam('u_team_id'))\
                .where(data_table.c.g_version == bindparam('u_g_version'))
            # we bind "u_g_id" (and others) as we cannot use "g_id" in the where clause for an
            # update. Passing this as an argument to db.execute doesn't cause any issue when we
            # use the insert query (that doesn't have u_g_id)
        db.execute(query_type,
                   g_id=gradeable_id, u_g_id=gradeable_id,
                   team_id=team_id, u_team_id=team_id,
                   g_version=version, u_g_version=version,
                   autograding_non_hidden_non_extra_credit=non_hidden_non_ec,
                   autograding_non_hidden_extra_credit=non_hidden_ec,
                   autograding_hidden_non_extra_credit=hidden_non_ec,
                   autograding_hidden_extra_credit=hidden_ec,
                   submission_time=submission_time,
                   autograding_complete=True)

    else:
        result = db.execute(select([func.count()]).select_from(data_table)
                            .where(data_table.c.g_id == bindparam('g_id'))
                            .where(data_table.c.user_id == bindparam('user_id'))
                            .where(data_table.c.g_version == bindparam('g_version')),
                            g_id=gradeable_id, user_id=user_id, g_version=version)
        row = result.fetchone()
        result.close()
        query_type = data_table.insert()
        if row[0] > 0:
            query_type = data_table\
                .update(
                    values={
                        data_table.c.autograding_non_hidden_non_extra_credit:
                            bindparam("autograding_non_hidden_non_extra_credit"),
                        data_table.c.autograding_non_hidden_extra_credit:
                            bindparam("autograding_non_hidden_extra_credit"),
                        data_table.c.autograding_hidden_non_extra_credit:
                            bindparam("autograding_hidden_non_extra_credit"),
                        data_table.c.autograding_hidden_extra_credit:
                            bindparam("autograding_hidden_extra_credit"),
                        data_table.c.autograding_complete:
                            bindparam("autograding_complete")
                    })\
                .where(data_table.c.g_id == bindparam('u_g_id'))\
                .where(data_table.c.user_id == bindparam('u_user_id'))\
                .where(data_table.c.g_version == bindparam('u_g_version'))
            # we bind "u_g_id" (and others) as we cannot use "g_id" in the where clause for an
            # update. Passing this as an argument to db.execute doesn't cause any issue when we
            # use the insert query (that doesn't have u_g_id)
        db.execute(query_type,
                   g_id=gradeable_id, u_g_id=gradeable_id,
                   user_id=user_id, u_user_id=user_id,
                   g_version=version, u_g_version=version,
                   autograding_non_hidden_non_extra_credit=non_hidden_non_ec,
                   autograding_non_hidden_extra_credit=non_hidden_ec,
                   autograding_hidden_non_extra_credit=hidden_non_ec,
                   autograding_hidden_extra_credit=hidden_ec,
                   submission_time=submission_time,
                   autograding_complete=True)
    db.close()
    engine.dispose()


def get_testcases(semester, course, g_id):
    """
    Get all the testcases for a homework from its build json file. This should have a 1-to-1
    correspondance with the testcases that come from the results.json file.

    :param semester:
    :param course:
    :param g_id:
    :return:
    """
    testcases = []
    build_file = os.path.join(DATA_DIR, "courses", semester, course, "config", "build",
                              "build_" + g_id + ".json")
    if os.path.isfile(build_file):
        with open(build_file) as build_file:
            build_json = json.load(build_file)
            if 'testcases' in build_json and build_json['testcases'] is not None:
                for testcase in build_json['testcases']:
                    testcases.append({'hidden': testcase['hidden'],
                                      'extra_credit': testcase['extra_credit'],
                                      'points': testcase['points']})
    return testcases


def get_result_details(semester, course, g_id, who_id, version):
    """
    Gets the result details for a particular version of a gradeable for the who (user or team).
    It returns a dictionary that contains a list of the testcases (that should have a 1-to-1
    correspondence with the testcases gotten through get_testcases() method) and the submission
    time for the particular version.

    :param semester:
    :param course:
    :param g_id:
    :param who_id:
    :param version:
    :return:
    """
    result_details = {'testcases': [], 'submission_time': None}
    result_dir = os.path.join(DATA_DIR, "courses", semester, course, "results", g_id, who_id,
                              str(version))
    if os.path.isfile(os.path.join(result_dir, "results.json")):
        with open(os.path.join(result_dir, "results.json")) as result_file:
            result_json = json.load(result_file)
            if 'testcases' in result_json and result_json['testcases'] is not None:
                for testcase in result_json['testcases']:
                    result_details['testcases'].append({'points': testcase['points_awarded']})

    if os.path.isfile(os.path.join(result_dir, "history.json")):
        with open(os.path.join(result_dir, "history.json")) as result_file:
            result_json = json.load(result_file)
            # a = datetime.strptime(result_json[-1]['submission_time'], "%a %b  %d %H:%M:%S %Z %Y")
            a = dateutils.read_submitty_date(result_json[-1]['submission_time'])
            result_details['submission_time'] = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}' \
                .format(a.year, a.month, a.day, a.hour, a.minute, a.second)
    return result_details
