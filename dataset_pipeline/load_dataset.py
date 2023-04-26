from s1_candidate_submissions import create_candidate_submissions_file
from s2_cleaned_dataset import create_cleaned_files
from s3_vector_dataset import create_vector_files
from s4_upload_data import upload_to_db
import multiprocessing
import glob

DIRECTORY = ""

def execute(args):
    directory, date = args
    # Download dataset
    create_candidate_submissions_file(directory, date)
    create_cleaned_files(directory, date)
    create_vector_files(directory, date)
    upload_to_db(directory, date)

if __name__ == "__main__":
    directory = DIRECTORY
    json_files = glob.glob(f"{directory}/2_CleanedDataset/QA_*.json")

    dates_to_load = [x.split('QA_')[1].replace('.json', '') for x in json_files]

    args_list = [(directory, date) for date in dates_to_load]
    with multiprocessing.Pool(processes=1) as pool:
        results = pool.map(execute, args_list)
        print(results)