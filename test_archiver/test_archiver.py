import argparse
import os.path
import sys


from archiver import Archiver
from output_parser import OutputParser, SUPPORTED_OUTPUT_FORMATS

def parse_metadata_args(metadata_args):
    metadata = {}
    if metadata_args:
        for item in metadata_args:
            try:
                name, value = item.split(':', 1)
                metadata[name] = value
            except Exception:
                raise Exception("Unsupported format for metadata: '{}' use NAME:VALUE".format(item))
    return metadata


def read_config_file(file_name):
    with open(file_name, 'r') as config_file:
        return json.load(config_file)


def parse_commandline_arguments():
    parser = argparse.ArgumentParser(description='Parse Robot Framework output.xml files to SQL database.')
    parser.add_argument('output_files', nargs='+')
    parser.add_argument('--config', dest='config_file',
                        help='path to JSON config file containing database credentials')
    parser.add_argument('--dbengine', default='sqlite',
                        help='Database engine, postgresql or sqlite (default)')
    parser.add_argument('--database', help='database name')
    parser.add_argument('--host', help='databse host name', default=None)
    parser.add_argument('--user', help='database user')
    parser.add_argument('--pw', '--password', help='database password')
    parser.add_argument('--port', help='database port (default: 5432)', default=5432, type=int)
    parser.add_argument('--format', help='output format (default: robotframework)', default='robotframework',
                        choices=SUPPORTED_OUTPUT_FORMATS, type=str.lower)
    parser.add_argument('--team', help='Team name for the test series', default=None)
    parser.add_argument('--series', action='append',
                        help="Name of the testseries (and optionally build number 'SERIES_NAME#BUILD_NUM')")
    parser.add_argument('--metadata', action='append',
                        help="Adds given metadata to the testrun. expected_format 'NAME:VALUE'")
    return parser.parse_args()

def parse_config_and_db_engine(args):
    if args.config_file:
        config = read_config_file(args.config_file)
        db_engine = config['db_engine']
    else:
        db_engine = args.dbengine
        config = {
            'database': args.database,
            'user': args.user,
            'password': args.pw,
            'host': args.host,
            'port': args.port,
            }
    config['series'] = args.series
    if args.team:
        config['team'] = args.team
    metadata = parse_metadata_args(args.metadata)
    if 'metadata' in config:
        config['metadata'].update(metadata)
    else:
        config['metadata'] = metadata
    if len(args.output_files) > 1:
        config['multirun'] = {}

    return config, db_engine

if __name__ == '__main__':
    if sys.version_info[0] < 3:
        sys.exit('Unsupported Python version (' + str(sys.version_info.major) + '). Please use version 3.')

    args = parse_commandline_arguments()
    config, db_engine = parse_config_and_db_engine(args)

    archiver = Archiver(db_engine, config)
    output_parser = OutputParser(archiver, args.output_files, args.format)
    output_parser.parse_output_files()
